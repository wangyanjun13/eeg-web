from pydantic import BaseModel
from typing import List, Dict, Optional, Tuple

class ERPParams(BaseModel):
    """ERP分析参数"""
    tmin: float = -0.2
    tmax: float = 1.0
    baseline: Optional[Tuple[float, float]] = (-0.2, 0)
    event_id: str = None

class TimeFreqParams(BaseModel):
    """时频分析参数"""
    freqs: List[float]
    n_cycles: int = 3
    method: str = "morlet"

class ConnectivityParams(BaseModel):
    """连接性分析参数"""
    method: str = "plv"
    fmin: float = 8
    fmax: float = 13 