from pydantic import BaseModel
from typing import List, Optional, Dict

class FilterParams(BaseModel):
    """滤波参数"""
    low_freq: float = 1.0
    high_freq: float = 40.0
    notch: bool = True
    notch_freq: float = 50.0

class ICAParams(BaseModel):
    """ICA参数"""
    n_components: Optional[int] = None
    random_state: int = 42

class ArtifactParams(BaseModel):
    """伪迹去除参数"""
    eog: bool = True
    ecg: bool = True
    threshold: float = 3.0

class PreprocessedData(BaseModel):
    """预处理后的数据"""
    data: Dict[str, List[float]]
    times: List[float]
    channels: List[str]
    applied_methods: List[str] 