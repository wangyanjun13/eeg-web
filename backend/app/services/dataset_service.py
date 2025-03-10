from pathlib import Path
import mne
import os
from typing import List, Optional
import pandas as pd
from app.models.data_dataset import DatasetInfo, RawDataInfo, RawEEGData, ParticipantInfo

class DatasetService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        if not self.data_dir.exists():
            raise ValueError(f"数据目录不存在: {self.data_dir}")

    def list_datasets(self) -> List[DatasetInfo]:
        """获取所有数据集列表"""
        datasets = []
        for dir_name in os.listdir(self.data_dir):
            if dir_name.startswith('sub-'):
                dataset = self._process_dataset_dir(dir_name)
                if dataset:
                    datasets.append(dataset)
        return sorted(datasets, key=lambda x: x.id)

    def _process_dataset_dir(self, dir_name: str) -> Optional[DatasetInfo]:
        """处理数据集目录，返回数据集信息"""
        try:
            subject_id = int(dir_name.split('-')[1])
            eeg_dir = self.data_dir / dir_name / 'eeg'
            if not eeg_dir.exists():
                return None

            set_files = list(eeg_dir.glob('*.set'))
            if not set_files:
                return None

            set_file = set_files[0]
            fdt_file = set_file.with_suffix('.fdt')

            return DatasetInfo(
                id=subject_id,
                name=set_file.name,
                subject=dir_name,
                format='EEGLAB',
                has_fdt=fdt_file.exists()
            )
        except Exception:
            return None

    def get_dataset_info(self, dataset_id: str) -> RawDataInfo:
        """获取数据集详细信息"""
        try:
            raw = self._read_eeg_file(dataset_id)
            return RawDataInfo(
                channels=raw.ch_names,
                sampling_rate=raw.info['sfreq'],
                duration=raw.times[-1],
                n_channels=len(raw.ch_names),
                subject_id=f"sub-{dataset_id}"
            )
        except Exception as e:
            raise ValueError(f"获取数据集信息失败: {str(e)}")

    def get_dataset_data(self, dataset_id: str, start_time: float = 0, duration: float = 10) -> RawEEGData:
        """获取数据集EEG数据片段"""
        raw = self._read_eeg_file(dataset_id)
        data, times = self._get_time_slice(raw, start_time, duration)
        return RawEEGData(
            data={ch: d.tolist() for ch, d in zip(raw.ch_names, data)},
            times=times.tolist(),
            channels=raw.ch_names,
            duration=raw.times[-1],
            sampling_rate=raw.info['sfreq']
        )

    def _read_eeg_file(self, dataset_id: str) -> mne.io.Raw:
        """读取EEG文件"""
        eeg_dir = self.data_dir / f"sub-{dataset_id}" / 'eeg'
        set_files = list(eeg_dir.glob('*.set'))
        if not set_files:
            raise FileNotFoundError(f"未找到EEG数据文件: {eeg_dir}")
        return mne.io.read_raw_eeglab(str(set_files[0]), preload=True)

    def _get_time_slice(self, raw: mne.io.Raw, start_time: float, duration: float):
        """获取指定时间段的数据"""
        start_idx = int(start_time * raw.info['sfreq'])
        end_idx = int((start_time + duration) * raw.info['sfreq'])
        data = raw.get_data()[:, start_idx:end_idx]
        times = raw.times[start_idx:end_idx]
        return data, times

    def get_participants_info(self) -> ParticipantInfo:
        """获取参与者信息"""
        try:
            df = pd.read_csv(self.data_dir.parent / "participants.tsv", sep='\t')
            return ParticipantInfo(
                total_count=len(df),
                group_stats=df.groupby('Group').agg({
                    'Age': ['mean', 'min', 'max'],
                    'Gender': 'count'
                }).to_dict()
            )
        except Exception as e:
            raise ValueError(f"读取参与者信息失败: {str(e)}")

    # ... 其他辅助方法 ... 