from pathlib import Path
import numpy as np
from app.models.data_preprocess import FilterParams, ICAParams, ArtifactParams, PreprocessedData
from scipy import signal
from app.models.data_dataset import RawEEGData
from mne.preprocessing import ICA

class PreprocessService:
    def __init__(self, dataset_service):
        self.dataset_service = dataset_service

    def apply_filter(self, dataset_id: str, subject_id: str, params: FilterParams) -> RawEEGData:
        """应用滤波器"""
        # 获取原始数据
        raw_data = self.dataset_service.get_subject_data(dataset_id, subject_id)
        
        if isinstance(raw_data, RawEEGData) and raw_data.error:
            raise ValueError(raw_data.error)

        # 设置滤波参数
        nyquist = raw_data.sampling_rate / 2
        low = params.low_freq / nyquist
        high = params.high_freq / nyquist
        
        # 应用滤波器
        filtered_data = {}
        for channel, signal_data in raw_data.data.items():
            # 带通滤波
            b, a = signal.butter(4, [low, high], btype='band')
            filtered = signal.filtfilt(b, a, signal_data)
            
            # 陷波滤波
            if params.notch:
                notch_b, notch_a = signal.iirnotch(params.notch_freq / nyquist, Q=30)
                filtered = signal.filtfilt(notch_b, notch_a, filtered)
            
            filtered_data[channel] = filtered.tolist()

        return RawEEGData(
            data=filtered_data,
            times=raw_data.times,
            channels=raw_data.channels,
            duration=raw_data.duration,
            sampling_rate=raw_data.sampling_rate,
            dataset_id=dataset_id,
            subject_id=subject_id
        )

    def run_ica(self, dataset_id: str, subject_id: str, params: ICAParams) -> RawEEGData:
        """运行ICA分析"""
        # 获取原始数据
        raw_data = self.dataset_service.get_subject_data(dataset_id, subject_id)
        
        # 转换为numpy数组
        data = np.array([raw_data.data[ch] for ch in raw_data.channels])
        
        # 运行ICA
        ica = ICA(
            n_components=params.n_components,
            random_state=params.random_state
        )
        ica.fit(data)
        
        # 应用ICA
        cleaned_data = ica.apply(data)
        
        # 转换回字典格式
        processed_data = {
            ch: cleaned_data[i].tolist()
            for i, ch in enumerate(raw_data.channels)
        }
        
        return RawEEGData(
            data=processed_data,
            times=raw_data.times,
            channels=raw_data.channels,
            duration=raw_data.duration,
            sampling_rate=raw_data.sampling_rate,
            dataset_id=dataset_id,
            subject_id=subject_id
        )

    def remove_artifacts(self, dataset_id: str, subject_id: str, params: ArtifactParams) -> RawEEGData:
        """去除伪迹"""
        # 获取原始数据
        raw_data = self.dataset_service.get_subject_data(dataset_id, subject_id)
        
        if isinstance(raw_data, RawEEGData) and raw_data.error:
            raise ValueError(raw_data.error)
        
        # 转换为numpy数组以便处理
        data_array = np.array([raw_data.data[ch] for ch in raw_data.channels])
        
        # 简单的阈值去伪迹方法
        if params.threshold > 0:
            # 计算每个通道的标准差
            channel_stds = np.std(data_array, axis=1)
            
            # 对每个通道应用阈值
            for i, ch in enumerate(raw_data.channels):
                # 获取当前通道数据
                channel_data = data_array[i]
                
                # 计算阈值（标准差的倍数）
                threshold = channel_stds[i] * params.threshold
                
                # 找出超过阈值的点
                artifacts = np.where(np.abs(channel_data) > threshold)[0]
                
                # 如果有伪迹点，用线性插值替换
                if len(artifacts) > 0:
                    # 创建一个掩码，标记非伪迹点
                    mask = np.ones(len(channel_data), dtype=bool)
                    mask[artifacts] = False
                    
                    # 使用非伪迹点进行插值
                    x = np.arange(len(channel_data))
                    channel_data_clean = np.interp(
                        x, 
                        x[mask], 
                        channel_data[mask]
                    )
                    
                    # 更新数据
                    data_array[i] = channel_data_clean
        
        # 转换回字典格式
        processed_data = {
            ch: data_array[i].tolist()
            for i, ch in enumerate(raw_data.channels)
        }
        
        return RawEEGData(
            data=processed_data,
            times=raw_data.times,
            channels=raw_data.channels,
            duration=raw_data.duration,
            sampling_rate=raw_data.sampling_rate,
            dataset_id=dataset_id,
            subject_id=subject_id
        ) 