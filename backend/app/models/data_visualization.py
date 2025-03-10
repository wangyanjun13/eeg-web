from pydantic import BaseModel
from typing import List, Optional, Tuple

class TopoMapParams(BaseModel):
    """地形图参数"""
    times: Optional[List[float]] = None
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    colormap: str = "RdBu_r"

class TimeSeriesParams(BaseModel):
    """时间序列图参数"""
    channels: Optional[List[str]] = None
    start_time: float = 0
    duration: float = 10
    ylim: Optional[Tuple[float, float]] = None

class SpectrumParams(BaseModel):
    """频谱图参数"""
    fmin: float = 0
    fmax: float = 50
    channels: Optional[List[str]] = None 