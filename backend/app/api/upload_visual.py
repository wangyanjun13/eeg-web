from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import shutil
from datetime import datetime
from pathlib import Path
from app.services.upload_visual_service import UploadService, ModelEvaluationService

router = APIRouter(prefix="/api/upload", tags=["upload"])

# 创建上传目录
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = UPLOAD_DIR / "data"
MODEL_DIR = UPLOAD_DIR / "models"

# 确保目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

print(f"上传目录: {UPLOAD_DIR}")
print(f"数据文件目录: {DATA_DIR}")
print(f"模型文件目录: {MODEL_DIR}")

# 实例化服务
upload_service = UploadService()
model_evaluation_service = ModelEvaluationService(upload_service)

@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),  # "data" 或 "model"
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file_format: Optional[str] = Form(None),  # 对于数据文件: "set", "fdt", "mat", "npy"; 对于模型文件: "h5"
):
    """
    上传数据文件或模型文件
    """
    # 验证文件类型
    if file_type not in ["data", "model"]:
        raise HTTPException(status_code=400, detail="文件类型必须是 'data' 或 'model'")
    
    # 根据文件类型选择保存目录
    upload_dir = DATA_DIR if file_type == "data" else MODEL_DIR
    
    # 获取文件扩展名
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    # 验证文件扩展名
    valid_data_extensions = [".set", ".fdt", ".mat", ".npy"]
    valid_model_extensions = [".h5"]
    
    if file_type == "data" and file_extension not in valid_data_extensions:
        raise HTTPException(status_code=400, detail="数据文件必须是 .set, .fdt, .mat 或 .npy 格式")
    
    if file_type == "model" and file_extension not in valid_model_extensions:
        raise HTTPException(status_code=400, detail="模型文件必须是 .h5 格式")
    
    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{file.filename}"
    file_path = upload_dir / unique_filename
    
    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
    
    # 检查文件是否成功保存
    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="文件保存失败")
    
    # 获取文件大小
    file_size = os.path.getsize(file_path)
    
    # 保存元数据
    metadata = {
        "name": name,
        "description": description,
        "original_filename": file.filename,
        "saved_filename": unique_filename,
        "file_type": file_type,
        "file_format": file_format or file_extension.replace(".", ""),
        "upload_time": timestamp,
        "file_size": file_size,
        "file_path": str(file_path)
    }
    
    print(f"准备保存文件元数据: {metadata}")
    
    # 将元数据保存到服务中
    file_id = upload_service.save_file_metadata(metadata)
    
    return {"status": "success", "message": "文件上传成功", "file_id": file_id, "metadata": metadata}

@router.get("/files")
async def get_uploaded_files(file_type: Optional[str] = None):
    """
    获取所有上传的文件列表
    可选参数 file_type 用于筛选 "data" 或 "model" 文件
    """
    files = upload_service.get_files(file_type)
    print(f"后端返回文件列表: {len(files)} 个文件")
    return {"status": "success", "files": files}

@router.get("/files/{file_id}")
async def get_file_details(file_id: str):
    """
    获取特定文件的详细信息
    """
    file_details = upload_service.get_file_by_id(file_id)
    if not file_details:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return {"status": "success", "file": file_details}

@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """
    删除文件
    """
    success = upload_service.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="文件不存在或删除失败")
    
    return {"status": "success", "message": "文件删除成功"}

@router.get("/files/{file_id}/download")
async def download_file(file_id: str):
    """
    下载文件
    """
    try:
        print(f"请求下载文件ID: {file_id}")
        file_details = upload_service.get_file_by_id(file_id)
        if not file_details:
            print(f"文件不存在: {file_id}")
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_path = file_details.get("file_path")
        print(f"文件路径: {file_path}")
        
        if not file_path or not os.path.exists(file_path):
            print(f"文件路径不存在: {file_path}")
            raise HTTPException(status_code=404, detail="文件不存在或已被删除")
        
        print(f"准备下载文件: {file_path}, 大小: {os.path.getsize(file_path)} 字节")
        
        original_filename = file_details.get("original_filename")
        # 确保文件名正确编码，特别是中文文件名
        filename = original_filename.encode('latin-1').decode('utf-8', errors='ignore')
        
        return FileResponse(
            path=file_path, 
            filename=filename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        print(f"下载文件时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")

@router.post("/evaluate_model")
async def evaluate_model(
    data_file_id: str = Form(...), 
    model_file_id: str = Form(...)
):
    """
    严格评估模型对EEG数据的处理效果
    
    直接使用上传的模型处理上传的数据，不使用任何后备处理方法
    """
    # 调用服务层的evaluate_model方法
    result = model_evaluation_service.evaluate_model(data_file_id, model_file_id)
    return result
