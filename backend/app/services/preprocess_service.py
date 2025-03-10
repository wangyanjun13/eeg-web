from pathlib import Path
import mne
from typing import List, Dict, Optional
from app.models.data_preprocess import (
    FilterParams, ICAParams, ArtifactParams, PreprocessedData
)

class PreprocessService:
    def __init__(self, dataset_service):
        self.dataset_service = dataset_service

    def apply_filter(self, dataset_id: str, params: FilterParams) -> PreprocessedData:
        """应用滤波器"""
        raw = self.dataset_service._read_eeg_file(dataset_id)
        
        # 应用带通滤波
        if params.low_freq and params.high_freq:
            raw.filter(params.low_freq, params.high_freq)
        
        # 应用陷波滤波
        if params.notch:
            raw.notch_filter(params.notch_freq)
            
        return self._convert_to_preprocessed_data(raw, ["filter"])

    def run_ica(self, dataset_id: str, params: ICAParams) -> PreprocessedData:
        """运行ICA分析"""
        raw = self.dataset_service._read_eeg_file(dataset_id)
        # ICA实现
        return self._convert_to_preprocessed_data(raw, ["ica"])

    def remove_artifacts(self, dataset_id: str, params: ArtifactParams) -> PreprocessedData:
        """去除伪迹"""
        raw = self.dataset_service._read_eeg_file(dataset_id)
        # 伪迹去除实现
        return self._convert_to_preprocessed_data(raw, ["artifact_removal"])

    def _convert_to_preprocessed_data(self, raw: mne.io.Raw, methods: List[str]) -> PreprocessedData:
        """转换为预处理数据格式"""
        data = raw.get_data()
        return PreprocessedData(
            data={ch: d.tolist() for ch, d in zip(raw.ch_names, data)},
            times=raw.times.tolist(),
            channels=raw.ch_names,
            applied_methods=methods
        ) 