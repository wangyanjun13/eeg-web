from pathlib import Path
import mne
import os
import json
from typing import List, Optional, Dict
import pandas as pd
from app.models.data_dataset import DatasetInfo, RawDataInfo, RawEEGData, ParticipantInfo
import numpy as np
import asyncio

class DatasetService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        if not self.data_dir.exists():
            raise ValueError(f"数据目录不存在: {self.data_dir}")

    def list_datasets(self, keyword: str = None) -> List[Dict]:
        """获取所有数据集列表，支持按名称或ID搜索"""
        datasets = []
        for dataset_dir in os.listdir(self.data_dir):
            if dataset_dir.startswith('ds'):
                dataset_info = self._get_dataset_metadata(dataset_dir)
                if dataset_info:
                    # 如果提供了关键词，则进行过滤
                    if keyword:
                        # 检查数据集ID是否包含关键词
                        id_match = keyword.lower() in dataset_info['dataset_id'].lower()
                        # 检查数据集名称是否包含关键词（不区分大小写）
                        name_match = ('Name' in dataset_info and 
                                    keyword.lower() in dataset_info['Name'].lower().replace('  ', ' '))
                        
                        # 如果既不匹配ID也不匹配名称，则跳过此数据集
                        if not (id_match or name_match):
                            continue
                    
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

    def get_subject_info(self, dataset_id: str, subject_id: str) -> Dict:
        """获取受试者详细信息"""
        try:
            # 读取EEG数据
            raw = self._read_eeg_file(dataset_id, subject_id)
            
            # 基本EEG信息
            info = {
                "channels": raw.ch_names,
                "sampling_rate": float(raw.info['sfreq']),  # 确保是Python原生float
                "duration": float(raw.times[-1]),  # 确保是Python原生float
                "n_channels": int(len(raw.ch_names)),  # 确保是Python原生int
                "subject_id": f"sub-{subject_id}",
                "dataset_id": dataset_id
            }
            
            # 尝试读取participants.tsv获取人口统计学信息
            try:
                participants_file = self.data_dir / dataset_id / "participants.tsv"
                if participants_file.exists():
                    df = pd.read_csv(participants_file, sep='\t')
                    # 查找当前受试者
                    participant_row = df[df['participant_id'] == f"sub-{subject_id}"]
                    
                    if not participant_row.empty:
                        # 添加可用的人口统计学信息，确保转换为Python原生类型
                        for col in df.columns:
                            if col != 'participant_id' and col in participant_row:
                                # 获取值并转换为Python原生类型
                                value = participant_row[col].values[0]
                                
                                # 根据数据类型进行转换
                                if pd.isna(value):
                                    # 处理NaN值
                                    info[col] = None
                                elif isinstance(value, (np.integer, np.int64)):
                                    info[col] = int(value)
                                elif isinstance(value, (np.floating, np.float64)):
                                    info[col] = float(value)
                                else:
                                    # 字符串和其他类型
                                    info[col] = str(value)
            except Exception as e:
                # 如果读取人口统计学信息失败，记录错误但继续返回EEG信息
                print(f"读取人口统计学信息失败: {str(e)}")
            
            return info
        except Exception as e:
            raise ValueError(f"获取受试者信息失败: {str(e)}")

    def get_subject_data(self, dataset_id: str, subject_id: str, start_time: float = 0, 
                        duration: float = 10, channels: list = None, 
                        cancel_event: asyncio.Event = None) -> RawEEGData:
        raw = None
        try:
            raw = self._read_eeg_file(dataset_id, subject_id)
            
            # 处理数据时定期检查取消事件
            def should_cancel():
                return cancel_event and cancel_event.is_set()
            
            # 在数据处理的关键点检查是否应该取消
            if should_cancel():
                return RawEEGData.error("请求已取消")
            
            # 验证时间范围
            max_time = raw.times[-1]
            if start_time >= max_time:
                return RawEEGData.error("请求的时间范围超出数据限制")
            
            # 调整持续时间
            if start_time + duration > max_time:
                duration = max_time - start_time
            
            # 通道筛选
            if channels:
                valid_channels = [ch for ch in channels if ch in raw.ch_names]
                if not valid_channels:
                    return RawEEGData.error("未找到有效的通道")
                raw.pick_channels(valid_channels)
            
            # 自动降采样
            if duration > 60:
                target_sfreq = min(raw.info['sfreq'], max(100, raw.info['sfreq'] / 2))
                if target_sfreq < raw.info['sfreq']:
                    raw.resample(target_sfreq)
            
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
            
        except MemoryError:
            return RawEEGData.error("系统资源不足，请缩小时间范围或减少通道数量")
        except Exception as e:
            return RawEEGData.error("数据处理失败，请稍后重试")
        finally:
            # 确保释放内存
            if raw is not None:
                del raw

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
        
        # 将电压单位从 V 转换为 μV (1V = 1,000,000μV)
        data = data * 1e6
        
        times = raw.times[start_idx:end_idx]
        return data, times

    def get_participants_info(self, dataset_id: str) -> Dict:
        """获取参与者信息"""
        try:
            participants_file = self.data_dir / dataset_id / "participants.tsv"
            if not participants_file.exists():
                return {
                    "total_count": 0,
                    "group_stats": {},
                    "participants": []
                }
                
            df = pd.read_csv(participants_file, sep='\t')
            
            # 将参与者数据转换为列表
            participants_list = []
            for _, row in df.iterrows():
                participant_dict = {}
                for col in df.columns:
                    value = row[col]
                    # 转换为Python原生类型
                    if pd.isna(value):
                        participant_dict[col] = None
                    elif isinstance(value, (np.integer, np.int64)):
                        participant_dict[col] = int(value)
                    elif isinstance(value, (np.floating, np.float64)):
                        participant_dict[col] = float(value)
                    else:
                        participant_dict[col] = str(value)
                participants_list.append(participant_dict)
            
            # 检查是否有Group列
            if 'Group' in df.columns:
                # 手动构建统计信息，确保所有键都是字符串
                group_stats = {}
                for group_name, group_df in df.groupby('Group'):
                    group_name_str = str(group_name)  # 确保键是字符串
                    group_stats[group_name_str] = {}
                    
                    if 'Age' in df.columns:
                        group_stats[group_name_str]['Age'] = {
                            'mean': float(group_df['Age'].mean()),
                            'min': float(group_df['Age'].min()),
                            'max': float(group_df['Age'].max())
                        }
                    
                    if 'Gender' in df.columns:
                        gender_counts = group_df['Gender'].value_counts().to_dict()
                        # 确保键是字符串
                        group_stats[group_name_str]['Gender'] = {
                            str(k): int(v) for k, v in gender_counts.items()
                        }
            else:
                # 如果没有Group列，创建基本统计信息
                group_stats = {'All': {}}
                
                if 'Age' in df.columns:
                    group_stats['All']['Age'] = {
                        'mean': float(df['Age'].mean()),
                        'min': float(df['Age'].min()),
                        'max': float(df['Age'].max())
                    }
                
                if 'Gender' in df.columns:
                    gender_counts = df['Gender'].value_counts().to_dict()
                    # 确保键是字符串
                    group_stats['All']['Gender'] = {
                        str(k): int(v) for k, v in gender_counts.items()
                    }
            
            # 返回字典，包含统计信息和完整的参与者列表
            return {
                "total_count": int(len(df)),
                "group_stats": group_stats,
                "participants": participants_list
            }
        except Exception as e:
            raise ValueError(f"读取参与者信息失败: {str(e)}")

    def get_electrode_positions(self, dataset_id: str, subject_id: str) -> Dict:
        """获取电极位置信息"""
        try:
            # 从.set文件读取电极位置
            raw = self._read_eeg_file(dataset_id, subject_id)
            
            # 提取通道位置信息
            positions = {}
            for i, ch_name in enumerate(raw.ch_names):
                # 获取通道信息
                ch_info = raw.info['chs'][i]
                
                # 检查是否有位置信息
                if ch_info['loc'] is not None and any(ch_info['loc'][:3]):
                    # 提取3D坐标 (x, y, z)
                    x, y, z = ch_info['loc'][:3]
                    positions[ch_name] = {
                        'x': float(x),
                        'y': float(y),
                        'z': float(z)
                    }
                    # print(f"通道 {ch_name} 位置: x={x}, y={y}, z={z}")
            
            # 如果没有位置信息，返回空字典
            if not positions:
                print("未找到任何电极位置信息")
                return {"positions": {}, "source": "none"}
            
            print(f"成功获取 {len(positions)} 个电极位置")
            return {
                "positions": positions,
                "source": "set_file"
            }
        except Exception as e:
            print(f"获取电极位置信息失败: {str(e)}")
            return {"positions": {}, "source": "error", "error": str(e)}


    async def stream_subject_data_direct(self, dataset_id: str, subject_id: str):
        """直接流式传输受试者数据，不预先生成完整ZIP文件"""
        import zipfile
        import io
        import os
        import asyncio
        
        # 获取受试者数据目录
        subject_dir = self.data_dir / dataset_id / f"sub-{subject_id}"
        
        # 创建一个ZipFile对象，但不立即写入所有文件
        zip_buffer = io.BytesIO()
        
        # 收集所有文件路径
        file_paths = []
        for root, _, files in os.walk(subject_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, str(self.data_dir / dataset_id))
                file_paths.append((file_path, arcname))
        
        # 创建ZIP文件头部信息
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 只添加一个小文件，让浏览器立即显示保存对话框
            info_content = f"Dataset: {dataset_id}\nSubject: {subject_id}\nFiles: {len(file_paths)}"
            zipf.writestr("info.txt", info_content)
        
        # 发送ZIP文件头部
        zip_buffer.seek(0)
        yield zip_buffer.getvalue()
        
        # 清空缓冲区，准备添加实际文件
        zip_buffer = io.BytesIO()
        
        # 分批处理文件
        batch_size = 5  # 每批处理5个文件
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for i in range(0, len(file_paths), batch_size):
                batch = file_paths[i:i+batch_size]
                
                # 添加文件到ZIP
                for file_path, arcname in batch:
                    zipf.write(file_path, arcname)
                
                # 获取当前批次的数据并发送
                zip_buffer.seek(0)
                yield zip_buffer.getvalue()
                
                # 重置缓冲区
                zip_buffer = io.BytesIO()
                
                # 让出控制权
                await asyncio.sleep(0.01)

    # ... 其他辅助方法 ... 