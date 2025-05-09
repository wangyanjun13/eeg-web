from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class DatasetInfo(BaseModel):
    """数据集基本信息"""
    id: str
    name: str
    subject_count: int
    format: str = "BIDS"

class RawDataInfo(BaseModel):
    """原始数据信息"""
    channels: List[str]
    sampling_rate: float
    duration: float
    n_channels: int
    subject_id: str
    dataset_id: str

class RawEEGData(BaseModel):
    """原始EEG数据"""
    data: Dict[str, List[float]]
    times: List[float]
    channels: List[str]
    duration: float
    sampling_rate: float
    dataset_id: Optional[str] = None
    subject_id: Optional[str] = None
    segment_info: Optional[Dict] = None
    timeRange: Optional[List[float]] = None
    error: Optional[str] = None
    
    @classmethod
    def error(cls, error_message: str):
        """创建带有错误信息的RawEEGData对象
        
        Args:
            error_message: 错误信息
            
        Returns:
            RawEEGData: 带有错误信息的对象
        """
        return cls(
            data={},
            times=[],
            channels=[],
            duration=0,
            sampling_rate=0,
            error=error_message
        )

class ParticipantInfo(BaseModel):
    """参与者信息"""
    total_count: int
    group_stats: Dict[str, Dict[str, Any]] = Field(default_factory=dict)