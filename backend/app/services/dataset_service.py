from pathlib import Path
import mne
import os
import json
from typing import List, Optional, Dict
import pandas as pd
from app.models.data_dataset import DatasetInfo, RawDataInfo, RawEEGData, ParticipantInfo

class DatasetService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        if not self.data_dir.exists():
            raise ValueError(f"数据目录不存在: {self.data_dir}")

    def list_datasets(self) -> List[Dict]:
        """获取所有数据集列表"""
        datasets = []
        for dataset_dir in os.listdir(self.data_dir):
            if dataset_dir.startswith('ds'):
                dataset_info = self._get_dataset_metadata(dataset_dir)
                if dataset_info:
                    datasets.append(dataset_info)
        return datasets

    def _get_dataset_metadata(self, dataset_dir: str) -> Dict:
        """从dataset_description.json获取数据集元数据"""
        try:
            desc_file = self.data_dir / dataset_dir / 'dataset_description.json'
            if not desc_file.exists():
                return None
                
            with open(desc_file, 'r') as f:
                metadata = json.load(f)
                
            # 添加数据集ID
            metadata['dataset_id'] = dataset_dir
            
            # 获取受试者数量
            subjects = [d for d in os.listdir(self.data_dir / dataset_dir) if d.startswith('sub-')]
            metadata['subject_count'] = len(subjects)
            
            return metadata
        except Exception as e:
            print(f"读取数据集元数据失败: {str(e)}")
            return None

    def get_dataset_subjects(self, dataset_id: str) -> List[Dict]:
        """获取指定数据集的所有受试者"""
        dataset_dir = self.data_dir / dataset_id
        if not dataset_dir.exists():
            raise ValueError(f"数据集不存在: {dataset_id}")
            
        subjects = []
        for dir_name in os.listdir(dataset_dir):
            if dir_name.startswith('sub-'):
                subject = self._process_subject_dir(dataset_id, dir_name)
                if subject:
                    subjects.append(subject)
        return sorted(subjects, key=lambda x: x['id'])

    def _process_subject_dir(self, dataset_id: str, dir_name: str) -> Optional[Dict]:
        """处理受试者目录，返回受试者信息"""
        try:
            subject_id = dir_name.split('-')[1]
            eeg_dir = self.data_dir / dataset_id / dir_name / 'eeg'
            if not eeg_dir.exists():
                return None

            set_files = list(eeg_dir.glob('*.set'))
            if not set_files:
                return None

            set_file = set_files[0]
            fdt_file = set_file.with_suffix('.fdt')

            return {
                'id': subject_id,
                'name': set_file.name,
                'subject': dir_name,
                'format': 'EEGLAB',
                'has_fdt': fdt_file.exists(),
                'dataset_id': dataset_id
            }
        except Exception:
            return None

    def get_dataset_info(self, dataset_id: str) -> Dict:
        """获取数据集详细信息"""
        try:
            # 获取数据集元数据
            metadata = self._get_dataset_metadata(dataset_id)
            if not metadata:
                raise ValueError(f"无法获取数据集元数据: {dataset_id}")
                
            # 获取受试者列表
            subjects = self.get_dataset_subjects(dataset_id)
            
            # 获取事件信息
            events_info = self._get_events_info(dataset_id)
            
            # 合并信息
            info = {
                **metadata,
                'subjects': subjects,
                'events': events_info
            }
            
            return info
        except Exception as e:
            raise ValueError(f"获取数据集信息失败: {str(e)}")

    def _get_events_info(self, dataset_id: str) -> Dict:
        """获取事件信息"""
        try:
            # 查找事件描述文件
            events_files = list((self.data_dir / dataset_id).glob('*_events.json'))
            if not events_files:
                return {}
                
            with open(events_files[0], 'r') as f:
                events_info = json.load(f)
            
            return events_info
        except Exception:
            return {}

    def get_subject_info(self, dataset_id: str, subject_id: str) -> RawDataInfo:
        """获取受试者详细信息"""
        try:
            raw = self._read_eeg_file(dataset_id, subject_id)
            return RawDataInfo(
                channels=raw.ch_names,
                sampling_rate=raw.info['sfreq'],
                duration=raw.times[-1],
                n_channels=len(raw.ch_names),
                subject_id=f"sub-{subject_id}",
                dataset_id=dataset_id
            )
        except Exception as e:
            raise ValueError(f"获取受试者信息失败: {str(e)}")

    def get_subject_data(self, dataset_id: str, subject_id: str, start_time: float = 0, duration: float = 10) -> RawEEGData:
        """获取受试者EEG数据片段"""
        raw = self._read_eeg_file(dataset_id, subject_id)
        data, times = self._get_time_slice(raw, start_time, duration)
        return RawEEGData(
            data={ch: d.tolist() for ch, d in zip(raw.ch_names, data)},
            times=times.tolist(),
            channels=raw.ch_names,
            duration=raw.times[-1],
            sampling_rate=raw.info['sfreq'],
            dataset_id=dataset_id,
            subject_id=subject_id
        )

    def _read_eeg_file(self, dataset_id: str, subject_id: str) -> mne.io.Raw:
        """读取EEG文件"""
        eeg_dir = self.data_dir / dataset_id / f"sub-{subject_id}" / 'eeg'
        if not eeg_dir.exists():
            raise FileNotFoundError(f"未找到EEG数据目录: {eeg_dir}")
            
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

    def get_participants_info(self, dataset_id: str) -> ParticipantInfo:
        """获取参与者信息"""
        try:
            participants_file = self.data_dir / dataset_id / "participants.tsv"
            if not participants_file.exists():
                return ParticipantInfo(
                    total_count=0,
                    group_stats={}
                )
                
            df = pd.read_csv(participants_file, sep='\t')
            
            # 检查是否有Group列
            if 'Group' in df.columns:
                group_stats = df.groupby('Group').agg({
                    'Age': ['mean', 'min', 'max'] if 'Age' in df.columns else [],
                    'Gender': 'count' if 'Gender' in df.columns else []
                }).to_dict()
            else:
                # 如果没有Group列，创建基本统计信息
                stats = {}
                if 'Age' in df.columns:
                    stats['Age'] = {
                        'mean': df['Age'].mean(),
                        'min': df['Age'].min(),
                        'max': df['Age'].max()
                    }
                if 'Gender' in df.columns:
                    stats['Gender'] = df['Gender'].value_counts().to_dict()
                    
                group_stats = {'All': stats}
            
            return ParticipantInfo(
                total_count=len(df),
                group_stats=group_stats
            )
        except Exception as e:
            raise ValueError(f"读取参与者信息失败: {str(e)}")

    # ... 其他辅助方法 ... 