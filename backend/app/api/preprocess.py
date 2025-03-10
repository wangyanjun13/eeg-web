from fastapi import APIRouter, HTTPException
from app.models.data_preprocess import FilterParams, ICAParams, ArtifactParams
from app.models.common import APIResponse
from app.services.preprocess_service import PreprocessService
from app.services.dataset_service import DatasetService
from pathlib import Path

# 创建服务实例
DATA_DIR = Path("/app/data/eeg_samples")
dataset_service = DatasetService(DATA_DIR)
preprocess_service = PreprocessService(dataset_service)

router = APIRouter(prefix="/api/preprocess")

@router.post("/{dataset_id}/filter", response_model=APIResponse)
async def apply_filter(dataset_id: str, params: FilterParams):
    """应用滤波器
    
    Args:
        dataset_id: 数据集ID
        params: 滤波参数
            - low_freq: 低频截止频率
            - high_freq: 高频截止频率
            - notch: 是否应用陷波滤波
            - notch_freq: 陷波频率（默认50Hz）
    """
    try:
        result = preprocess_service.apply_filter(dataset_id, params)
        return APIResponse(
            message="滤波处理完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/ica", response_model=APIResponse)
async def run_ica(dataset_id: str, params: ICAParams):
    """运行ICA分析
    
    Args:
        dataset_id: 数据集ID
        params: ICA参数
            - n_components: ICA组件数量
            - random_state: 随机数种子
    """
    try:
        result = preprocess_service.run_ica(dataset_id, params)
        return APIResponse(
            message="ICA分析完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/artifacts", response_model=APIResponse)
async def remove_artifacts(dataset_id: str, params: ArtifactParams):
    """去除伪迹
    
    Args:
        dataset_id: 数据集ID
        params: 伪迹去除参数
            - eog: 是否去除眼电伪迹
            - ecg: 是否去除心电伪迹
            - threshold: 伪迹检测阈值
    """
    try:
        result = preprocess_service.remove_artifacts(dataset_id, params)
        return APIResponse(
            message="伪迹去除完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/status", response_model=APIResponse)
async def get_preprocess_status(dataset_id: str):
    """获取预处理状态
    
    Args:
        dataset_id: 数据集ID
    """
    try:
        return APIResponse(
            message="获取预处理状态成功",
            data={
                "dataset_id": dataset_id,
                "applied_methods": [],  # 已应用的预处理方法
                "available_methods": [  # 可用的预处理方法
                    "filter",
                    "ica",
                    "artifacts"
                ]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 