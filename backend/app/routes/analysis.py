from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.eeg_service import EEGService
from pathlib import Path
import numpy as np
import mne

# 定义预处理参数模型
class PreprocessParams(BaseModel):
    filter_enabled: bool = False
    low_freq: float = 1.0
    high_freq: float = 40.0
    remove_bad_channels: bool = False

router = APIRouter(prefix="/api/datasets")

# 不在这里初始化 EEGService
# 改为在 main.py 中初始化并传入
eeg_service = None  # 将在main.py中设置

def init_eeg_service(data_dir: Path):
    global eeg_service
    eeg_service = EEGService(data_dir)

@router.get("/{dataset_id}/basic")
async def get_basic_info(dataset_id: str):
    try:
        raw = eeg_service.read_eeg_data(dataset_id)
        return {
            "sampling_rate": raw.info['sfreq'],
            "duration": raw.times[-1],
            "channels": raw.ch_names,
            "n_channels": len(raw.ch_names)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/preprocess")
async def preprocess_eeg(
    dataset_id: str,
    params: PreprocessParams
):
    try:
        # 读取EEG数据
        raw = eeg_service.read_eeg_data(dataset_id)
        
        # 应用滤波器
        if params.filter_enabled:
            raw.filter(params.low_freq, params.high_freq)
            
        # 去除坏导
        if params.remove_bad_channels:
            raw.interpolate_bads()
            
        # 返回处理后的数据
        return {"message": "预处理完成", "data": raw_to_dict(raw)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/time_freq")
async def compute_time_frequency(
    dataset_id: str,
    start_time: float = 0,
    duration: float = 10,
    method: str = "multitaper"
):
    try:
        raw = eeg_service.read_eeg_data(dataset_id)
        epochs = mne.make_fixed_length_epochs(raw, duration=duration)
        
        # 计算时频图
        freqs = np.logspace(*np.log10([6, 35]), num=20)
        power = mne.time_frequency.tfr_multitaper(
            epochs, freqs=freqs, n_cycles=2, return_itc=False
        )
        
        return {
            "frequencies": freqs.tolist(),
            "times": power.times.tolist(),
            "power": power.data.tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 辅助函数：将Raw对象转换为字典
def raw_to_dict(raw):
    return {
        "data": raw.get_data().tolist(),
        "times": raw.times.tolist(),
        "channels": raw.ch_names,
        "sampling_rate": raw.info['sfreq']
    } 