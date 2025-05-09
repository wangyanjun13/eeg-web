from pydantic import BaseModel
from typing import List, Optional, Dict, Union

class FilterParams(BaseModel):
    """滤波参数"""
    highpass_filter: bool = True
    highpass: float = 1.0
    lowpass_filter: bool = True
    lowpass: float = 40.0
    notch_filter: bool = True
    line_freqs: List[float] = [50.0, 60.0]

class ResampleParams(BaseModel):
    """重采样参数"""
    resample: bool = True
    resample_freq: float = 250.0

class ReferenceParams(BaseModel):
    """重参考参数"""
    reference: str = "average"  # "average", "mastoids", "custom"
    custom_ref_channels: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    time_range: Optional[List[float]] = None  # 添加时间范围参数，用于保持处理前后一致性

class ICAParams(BaseModel):
    """ICA参数"""
    run_ica: bool = True
    ica_method: str = "fastica"
    n_components: Optional[int] = None
    auto_detect_artifacts: bool = True

class BadChannelParams(BaseModel):
    """坏通道检测参数"""
    detect_bad_channels: bool = True
    bad_channel_method: str = "correlation"  # "correlation", "variance", "spectrum"
    threshold: Optional[float] = None  # 检测阈值，None表示使用默认值
    rejection_mode: str = "zero"  # "zero", "interpolate", "remove"
    use_custom_bads: bool = False  # 是否使用自定义坏通道列表
    custom_bad_channels: Optional[List[str]] = None  # 自定义坏通道列表

class ArtifactParams(BaseModel):
    """伪迹处理参数"""
    remove_artifacts: bool = True
    artifact_detection_method: str = "auto"  # "auto", "manual", "threshold"
    amplitude_threshold: Optional[float] = 100.0  # μV
    reject_by_annotation: bool = True

class SegmentParams(BaseModel):
    """数据分段参数"""
    segment_mode: str = "time"  # "time"或"event"
    use_original_full_data: bool = False
    # 时间窗口模式参数
    start_time: float = 0.0
    end_time: float = 10.0
    # 事件模式参数
    event_id: Optional[str] = None  # 事件类型ID
    time_before: float = 0.2  # 事件前时间
    time_after: float = 0.8  # 事件后时间
    # 基线校正参数
    apply_baseline: bool = True
    baseline_start: float = -0.2
    baseline_end: float = 0.0

class BadSegmentParams(BaseModel):
    """坏段检测参数"""
    detect_bad_segments: bool = True
    detection_method: str = "auto"  # "auto", "threshold", "manual"
    amplitude_threshold: float = 100.0  # μV
    gradient_threshold: float = 10.0  # μV/ms
    reject_method: str = "zero"  # "zero", "interpolate", "remove"

class PreprocessParams(BaseModel):
    """预处理参数集合"""
    filter: FilterParams = FilterParams()
    resample: ResampleParams = ResampleParams()
    segment: SegmentParams = SegmentParams()
    bad_channels: BadChannelParams = BadChannelParams()
    bad_segments: BadSegmentParams = BadSegmentParams()
    reference: ReferenceParams = ReferenceParams()
    ica: ICAParams = ICAParams()
    artifacts: ArtifactParams = ArtifactParams()
    
    # 预定义模板
    @classmethod
    def get_template(cls, template_name: str = "default") -> "PreprocessParams":
        templates = {
            "default": cls(),
            "minimal": cls(
                filter=FilterParams(highpass=0.5, lowpass=30.0),
                resample=ResampleParams(resample=False),
                ica=ICAParams(run_ica=False)
            ),
            "ds002218": cls(
                filter=FilterParams(highpass=1.0, lowpass=40.0, line_freqs=[60.0, 120.0]),
                resample=ResampleParams(resample_freq=256.0),
                reference=ReferenceParams(reference="average"),
                ica=ICAParams(run_ica=True)
            )
        }
        return templates.get(template_name, cls())

class PreprocessedData(BaseModel):
    """预处理后的数据"""
    data: Dict[str, List[float]]
    times: List[float]
    channels: List[str]
    applied_methods: List[str]
    params: PreprocessParams 