from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Any

class ERPParams(BaseModel):
    """ERP分析参数"""
    tmin: float = -0.2
    tmax: float = 1.0
    baseline: Optional[List[float]] = Field(default=[-0.2, 0], description="基线校正区间 [start, end]")
    event_id: Optional[str] = None
    # 预处理数据相关字段
    use_preprocessed_data: bool = False
    preprocessed_data: Optional[Dict[str, Any]] = None
    preprocess: bool = False
    preprocess_params: Optional[Dict[str, Any]] = None

class TimeFreqParams(BaseModel):
    """时频分析参数"""
    freqs: List[float]
    n_cycles: int = 3
    method: str = "morlet"
    # 预处理数据相关字段
    use_preprocessed_data: bool = False
    preprocessed_data: Optional[Dict[str, Any]] = None
    preprocess: bool = False
    preprocess_params: Optional[Dict[str, Any]] = None

class ConnectivityParams(BaseModel):
    """连接性分析参数"""
    method: str = "plv"
    fmin: float = 8
    fmax: float = 13
    # 预处理数据相关字段
    use_preprocessed_data: bool = False
    preprocessed_data: Optional[Dict[str, Any]] = None
    preprocess: bool = False
    preprocess_params: Optional[Dict[str, Any]] = None

class SpatialParams(BaseModel):
    """空间分析参数"""
    # 通道和频率选择
    channels: List[str]
    frequencyBand: str = "alpha"  # delta, theta, alpha, beta, gamma
    timePoint: Optional[float] = None  # 选择的时间点（毫秒）
    
    # 插值设置
    interpolation: Dict[str, Any] = Field(default_factory=lambda: {
        "method": "spline",        # spline, linear, nearest
        "resolution": 64           # 插值分辨率
    })
    
    # 显示设置
    display: Dict[str, Any] = Field(default_factory=lambda: {
        "colorMap": "jet",         # jet, viridis, plasma, inferno
        "showContour": True,       # 显示等高线
        "showElectrodes": True,    # 显示电极位置
        "normalize": False         # 归一化
    })
    
    # 预处理数据相关字段
    use_preprocessed_data: bool = False
    preprocessed_data: Optional[Dict[str, Any]] = None
    preprocess: bool = False
    preprocess_params: Optional[Dict[str, Any]] = None 