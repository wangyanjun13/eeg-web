from fastapi import APIRouter, HTTPException
from app.models.data_analysis import ERPParams, TimeFreqParams
from app.models.common import APIResponse
from app.services.analysis_service import AnalysisService
from app.services.dataset_service import DatasetService
from pathlib import Path

# 创建服务实例
DATA_DIR = Path("/app/data/eeg_samples")
dataset_service = DatasetService(DATA_DIR)
analysis_service = AnalysisService(dataset_service)

router = APIRouter(prefix="/api/analysis")

@router.get("/{dataset_id}/basic", response_model=APIResponse)
async def get_basic_info(dataset_id: str):
    """获取基本分析信息"""
    try:
        info = analysis_service.get_basic_info(dataset_id)
        return APIResponse(
            message="获取基本信息成功",
            data=info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/subjects/{subject_id}/erp", response_model=APIResponse)
async def compute_erp(dataset_id: str, subject_id: str, params: ERPParams):
    """计算ERP分析"""
    try:
        result = analysis_service.compute_erp(dataset_id, subject_id, params)
        return APIResponse(
            message="ERP分析完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/subjects/{subject_id}/time_freq", response_model=APIResponse)
async def compute_time_frequency(dataset_id: str, subject_id: str, params: TimeFreqParams):
    """计算时频分析"""
    try:
        result = analysis_service.compute_time_freq(dataset_id, subject_id, params)
        return APIResponse(
            message="时频分析完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 