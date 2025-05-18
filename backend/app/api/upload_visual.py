from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
import os
import logging
import traceback
from pathlib import Path
from app.services.upload_visual_service import UploadService, ModelEvaluationService, FileUploadService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("upload_api")

router = APIRouter(prefix="/api/upload", tags=["upload"])

# 创建上传目录
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = UPLOAD_DIR / "data"
MODEL_DIR = UPLOAD_DIR / "models"
TEMP_DIR = UPLOAD_DIR / "temp"  # 临时文件目录，用于大文件上传

# 确保目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"上传目录: {UPLOAD_DIR}")
logger.info(f"数据文件目录: {DATA_DIR}")
logger.info(f"模型文件目录: {MODEL_DIR}")
logger.info(f"临时文件目录: {TEMP_DIR}")

# 实例化服务
upload_service = UploadService()
model_evaluation_service = ModelEvaluationService(upload_service)
file_upload_service = FileUploadService(DATA_DIR, MODEL_DIR, TEMP_DIR, upload_service)

@router.post("/file")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    file_type: str = Form(...),  # "data" 或 "model"
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file_format: Optional[str] = Form(None),  # 对于数据文件: "set", "fdt", "mat", "npy"; 对于模型文件: "h5"
):
    """
    上传数据文件或模型文件
    """
    try:
        # 检查客户端连接类型
        client_headers = request.headers
        is_http2 = file_upload_service.check_http2_connection(client_headers)
        
        # 调用服务层处理文件上传
        response_data = await file_upload_service.process_file_upload(
            file, file_type, name, description, file_format, 
            is_http2, background_tasks
        )
        
        # 返回成功响应
        return JSONResponse(
            status_code=200,
            content=response_data
        )
    
    except HTTPException as http_ex:
        # 重新抛出HTTP异常
        logger.error(f"HTTP异常: {http_ex.detail}")
        raise
    
    except Exception as e:
        # 处理所有其他异常
        logger.error(f"处理上传文件时发生未捕获的异常: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 检查是否为HTTP/2协议错误
        error_str = str(e).lower()
        if "http2" in error_str or "protocol_error" in error_str:
            raise HTTPException(status_code=500, detail="网络传输错误，请尝试减小文件大小或使用HTTP/1.1连接")
        
        raise HTTPException(status_code=500, detail=f"上传处理失败: {str(e)}")

@router.get("/files")
async def get_uploaded_files(file_type: Optional[str] = None):
    """
    获取所有上传的文件列表
    可选参数 file_type 用于筛选 "data" 或 "model" 文件
    """
    try:
        files = upload_service.get_files(file_type)
        logger.info(f"后端返回文件列表: {len(files)} 个文件")
        return {"status": "success", "files": files}
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@router.get("/files/{file_id}")
async def get_file_details(file_id: str):
    """
    获取特定文件的详细信息
    """
    try:
        file_details = upload_service.get_file_by_id(file_id)
        if not file_details:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return {"status": "success", "file": file_details}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件详情失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取文件详情失败: {str(e)}")

@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """
    删除文件
    """
    try:
        success = upload_service.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="文件不存在或删除失败")
        
        return {"status": "success", "message": "文件删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

@router.get("/files/{file_id}/download")
async def download_file(file_id: str):
    """
    下载文件
    """
    try:
        logger.info(f"请求下载文件ID: {file_id}")
        file_details = upload_service.get_file_by_id(file_id)
        if not file_details:
            logger.error(f"文件不存在: {file_id}")
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_path = file_details.get("file_path")
        logger.info(f"文件路径: {file_path}")
        
        if not file_path or not os.path.exists(file_path):
            logger.error(f"文件路径不存在: {file_path}")
            raise HTTPException(status_code=404, detail="文件不存在或已被删除")
        
        file_size = os.path.getsize(file_path)
        logger.info(f"准备下载文件: {file_path}, 大小: {file_size / (1024 * 1024):.2f} MB")
        
        original_filename = file_details.get("original_filename")
        # 确保文件名正确编码，特别是中文文件名
        filename = original_filename.encode('latin-1').decode('utf-8', errors='ignore')
        
        return FileResponse(
            path=file_path, 
            filename=filename,
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件时出错: {str(e)}")
        logger.error(traceback.format_exc())
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
    try:
        # 调用服务层的evaluate_model方法
        logger.info(f"开始评估模型: 数据文件ID={data_file_id}, 模型文件ID={model_file_id}")
        result = model_evaluation_service.evaluate_model(data_file_id, model_file_id)
        return result
    except Exception as e:
        logger.error(f"评估模型时出错: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"评估模型失败: {str(e)}")
