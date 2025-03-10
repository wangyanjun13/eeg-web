from fastapi import APIRouter, HTTPException
from app.models.data_dataset import DatasetInfo, RawDataInfo, RawEEGData
from app.models.common import APIResponse
from app.services.dataset_service import DatasetService
from pathlib import Path

# 创建服务实例
DATA_DIR = Path("/app/data/eeg_samples")
dataset_service = DatasetService(DATA_DIR)

router = APIRouter(prefix="/api/datasets")

@router.get("/", response_model=APIResponse)
async def list_datasets():
    """获取所有数据集列表"""
    try:
        datasets = dataset_service.list_datasets()
        return APIResponse(
            message="获取数据集列表成功",
            data=datasets
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/info", response_model=APIResponse)
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

@router.get("/{dataset_id}/raw", response_model=APIResponse)
async def get_dataset_data(dataset_id: str, start_time: float = 0, duration: float = 10):
    """获取原始EEG数据"""
    try:
        data = dataset_service.get_dataset_data(dataset_id, start_time, duration)
        return APIResponse(
            message="获取原始数据成功",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/participants", response_model=APIResponse)
async def get_participants_info():
    """获取受试者信息"""
    try:
        participants = dataset_service.get_participants_info()
        return APIResponse(
            message="获取受试者信息成功",
            data=participants
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 