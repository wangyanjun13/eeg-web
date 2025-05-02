from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from app.models.data_dataset import DatasetInfo, RawDataInfo, RawEEGData
from app.models.common import APIResponse
from app.services.dataset_service import DatasetService
from pathlib import Path
import asyncio
import io

# 创建服务实例
DATA_DIR = Path("/app/data/eeg_samples")
dataset_service = DatasetService(DATA_DIR)

router = APIRouter(prefix="/api/datasets")

@router.get("/", response_model=APIResponse)
async def list_datasets(keyword: str = None):
    """获取所有数据集列表，支持按名称或ID搜索"""
    try:
        datasets = dataset_service.list_datasets(keyword)
        return APIResponse(
            message="获取数据集列表成功",
            data=datasets
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}", response_model=APIResponse)
async def get_dataset_info(dataset_id: str):
    """获取数据集详细信息"""
    try:
        info = dataset_service.get_dataset_info(dataset_id)
        return APIResponse(
            message="获取数据集信息成功",
            data=info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/subjects", response_model=APIResponse)
async def get_dataset_subjects(dataset_id: str):
    """获取数据集中的所有受试者"""
    try:
        subjects = dataset_service.get_dataset_subjects(dataset_id)
        return APIResponse(
            message="获取受试者列表成功",
            data=subjects
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/subjects/{subject_id}/info", response_model=APIResponse)
async def get_subject_info(dataset_id: str, subject_id: str):
    """获取受试者详细信息"""
    try:
        info = dataset_service.get_subject_info(dataset_id, subject_id)
        return APIResponse(
            message="获取受试者信息成功",
            data=info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/subjects/{subject_id}/raw", response_model=APIResponse)
async def get_subject_data(
    request: Request,
    background_tasks: BackgroundTasks,
    dataset_id: str, 
    subject_id: str, 
    start_time: float = 0, 
    duration: float = 10, 
    channels: str = None
):
    """获取受试者原始EEG数据"""
    try:
        # 设置请求超时（例如30秒）
        timeout = 30.0
        
        # 创建取消事件
        cancel_event = asyncio.Event()
        
        # 检查请求是否已断开
        async def is_disconnected():
            return await request.is_disconnected()
        
        # 超时或断开连接时取消任务
        async def watch_for_cancel():
            try:
                await asyncio.wait_for(cancel_event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                pass
            cancel_event.set()
        
        # 启动监控任务
        background_tasks.add_task(watch_for_cancel)
        
        # 将取消事件传递给服务层
        data = dataset_service.get_subject_data(
            dataset_id, subject_id, start_time, duration, channels, cancel_event
        )
        return APIResponse(message="获取原始数据成功", data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/participants", response_model=APIResponse)
async def get_participants_info(dataset_id: str):
    """获取数据集参与者信息"""
    try:
        participants = dataset_service.get_participants_info(dataset_id)
        return APIResponse(
            message="获取参与者信息成功",
            data=participants
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/subjects/{subject_id}/electrodes", response_model=APIResponse)
async def get_electrode_positions(dataset_id: str, subject_id: str):
    """获取电极位置信息"""
    try:
        positions = dataset_service.get_electrode_positions(dataset_id, subject_id)
        return APIResponse(
            message="获取电极位置信息成功",
            data=positions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/subjects/{subject_id}/export")
async def export_subject_data(dataset_id: str, subject_id: str):
    """导出受试者原始EEG数据"""
    try:
        # 检查受试者目录是否存在
        subject_dir = dataset_service.data_dir / dataset_id / f"sub-{subject_id}"
        if not subject_dir.exists():
            raise HTTPException(status_code=404, detail=f"未找到受试者数据目录: {subject_dir}")
            
        # 使用StreamingResponse，但不预先生成整个ZIP文件
        return StreamingResponse(
            dataset_service.stream_subject_data_direct(dataset_id, subject_id),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{dataset_id}_sub-{subject_id}_data.zip"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/subjects/{subject_id}/events", response_model=APIResponse)
async def get_subject_events(dataset_id: str, subject_id: str):
    """获取受试者的事件信息
    
    Args:
        dataset_id: 数据集ID
        subject_id: 受试者ID
    """
    try:
        events = dataset_service.get_events_info(dataset_id, subject_id)
        return APIResponse(
            message="获取事件信息成功",
            data=events
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
