from fastapi import APIRouter, HTTPException
from app.models.data_visualization import TimeSeriesParams
from app.models.common import APIResponse
from app.services.visualization_service import VisualService
from app.services.dataset_service import DatasetService
from pathlib import Path

# 创建服务实例
DATA_DIR = Path("/app/data/eeg_samples")
dataset_service = DatasetService(DATA_DIR)
visual_service = VisualService(dataset_service)

router = APIRouter(prefix="/api/visualization")

@router.get("/{dataset_id}/plot", response_model=APIResponse)
async def get_eeg_plot(dataset_id: str, start_time: float = 0, duration: float = 10):
    """获取EEG图表数据"""
    try:
        params = TimeSeriesParams(start_time=start_time, duration=duration)
        plot_data = visual_service.create_time_series(dataset_id, params)
        return APIResponse(
            message="获取EEG图表成功",
            data=plot_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 