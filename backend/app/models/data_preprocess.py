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

class ICAParams(BaseModel):
    """ICA参数"""
    run_ica: bool = True
    ica_method: str = "fastica"
    n_components: Optional[int] = None
    auto_detect_artifacts: bool = True

class BadChannelParams(BaseModel):
    """坏通道检测参数"""
    detect_bad_channels: bool = True
    bad_channel_method: str = "correlation"

class ArtifactParams(BaseModel):
    """伪迹处理参数"""
    remove_artifacts: bool = True
    artifact_detection_method: str = "auto"  # "auto", "manual", "threshold"
    amplitude_threshold: Optional[float] = 100.0  # μV
    reject_by_annotation: bool = True

class PreprocessParams(BaseModel):
    """预处理参数集合"""
    filter: FilterParams = FilterParams()
    resample: ResampleParams = ResampleParams()
    reference: ReferenceParams = ReferenceParams()
    ica: ICAParams = ICAParams()
    bad_channels: BadChannelParams = BadChannelParams()
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