from pathlib import Path
import numpy as np
from app.models.data_preprocess import FilterParams, ICAParams, ArtifactParams, PreprocessedData, PreprocessParams
from scipy import signal
from app.models.data_dataset import RawEEGData
from mne.preprocessing import ICA
import mne
from typing import Dict, List, Optional, Tuple

class PreprocessService:
    def __init__(self, dataset_service):
        self.dataset_service = dataset_service
        # 不依赖AnalysisService，避免循环依赖

    def apply_filter(self, dataset_id: str, subject_id: str, params: FilterParams) -> RawEEGData:
        """应用滤波器"""
        try:
            # 获取原始数据
            raw_data = self.dataset_service.get_subject_data(dataset_id, subject_id)
            
            if isinstance(raw_data, RawEEGData) and hasattr(raw_data, 'error') and raw_data.error:
                raise ValueError(raw_data.error)

            # 确保数据是有效的
            if not raw_data or not raw_data.data or not raw_data.channels:
                raise ValueError(f"无法获取有效的EEG数据: dataset_id={dataset_id}, subject_id={subject_id}")

            # 设置滤波参数
            nyquist = raw_data.sampling_rate / 2
            filtered_data = {}
            
            for channel, signal_data in raw_data.data.items():
                try:
                    data = np.array(signal_data)
                    
                    # 应用高通滤波
                    if params.highpass_filter and params.highpass > 0:
                        high_b, high_a = signal.butter(4, params.highpass / nyquist, btype='high')
                        data = signal.filtfilt(high_b, high_a, data)
                    
                    # 应用低通滤波
                    if params.lowpass_filter and params.lowpass > 0:
                        low_b, low_a = signal.butter(4, params.lowpass / nyquist, btype='low')
                        data = signal.filtfilt(low_b, low_a, data)
                    
                    # 应用陷波滤波
                    if params.notch_filter and params.line_freqs:
                        for freq in params.line_freqs:
                            if 0 < freq < nyquist:
                                notch_b, notch_a = signal.iirnotch(freq / nyquist, Q=30)
                                data = signal.filtfilt(notch_b, notch_a, data)
                    
                    filtered_data[channel] = data.tolist()
                except Exception as e:
                    print(f"处理通道 {channel} 时出错: {str(e)}")
                    # 如果处理失败，保留原始数据
                    filtered_data[channel] = signal_data

            return RawEEGData(
                data=filtered_data,
                times=raw_data.times,
                channels=raw_data.channels,
                duration=raw_data.duration,
                sampling_rate=raw_data.sampling_rate,
                dataset_id=dataset_id,
                subject_id=subject_id
            )
        except Exception as e:
            error_msg = f"滤波处理失败: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)

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

    def preprocess_eeg(self, raw, params: Optional[PreprocessParams] = None) -> Tuple[mne.io.Raw, PreprocessParams, List[str]]:
        """
        执行EEG预处理流程
        
        参数:
        - raw: MNE Raw对象
        - params: 预处理参数，如果为None则使用默认参数
        
        返回:
        - 处理后的Raw对象
        - 使用的预处理参数
        - 应用的处理方法列表
        """
        # 使用默认参数或用户提供的参数
        if params is None:
            params = PreprocessParams.get_template("default")
            
        # 记录应用的处理方法
        applied_methods = []
            
        # 1. 重采样
        if params.resample.resample:
            raw = raw.resample(params.resample.resample_freq)
            applied_methods.append(f"重采样至{params.resample.resample_freq}Hz")
        
        # 2. 高通滤波
        if params.filter.highpass_filter:
            raw = raw.filter(l_freq=params.filter.highpass, h_freq=None)
            applied_methods.append(f"高通滤波{params.filter.highpass}Hz")
        
        # 3. 低通滤波
        if params.filter.lowpass_filter:
            raw = raw.filter(l_freq=None, h_freq=params.filter.lowpass)
            applied_methods.append(f"低通滤波{params.filter.lowpass}Hz")
        
        # 4. 陷波滤波
        if params.filter.notch_filter:
            raw = raw.notch_filter(freqs=params.filter.line_freqs)
            applied_methods.append(f"陷波滤波{params.filter.line_freqs}Hz")
        
        # 5. 坏通道检测
        if params.bad_channels.detect_bad_channels:
            bads = self._detect_bad_channels(raw, method=params.bad_channels.bad_channel_method)
            raw.info['bads'] = bads
            applied_methods.append(f"坏通道检测({params.bad_channels.bad_channel_method})")
        
        # 6. 重参考
        if params.reference.reference == "average":
            raw = raw.set_eeg_reference('average', projection=False)
            applied_methods.append("平均重参考")
        elif params.reference.reference == "mastoids":
            raw = raw.set_eeg_reference(['M1', 'M2'], projection=False)
            applied_methods.append("双侧乳突参考")
        elif params.reference.reference == "custom" and params.reference.custom_ref_channels:
            raw = raw.set_eeg_reference(params.reference.custom_ref_channels, projection=False)
            applied_methods.append(f"自定义参考({','.join(params.reference.custom_ref_channels)})")
        
        # 7. ICA去伪迹
        if params.ica.run_ica:
            ica = self._run_ica(raw, 
                               n_components=params.ica.n_components,
                               method=params.ica.ica_method)
            
            # 自动检测眨眼伪迹
            if params.ica.auto_detect_artifacts:
                eog_indices = self._find_eog_artifacts(ica, raw)
                ica.exclude = eog_indices
                applied_methods.append(f"ICA去伪迹({params.ica.ica_method}，自动检测)")
            else:
                applied_methods.append(f"ICA去伪迹({params.ica.ica_method})")
                
            # 应用ICA
            raw = ica.apply(raw)
        
        return raw, params, applied_methods
    
    def _detect_bad_channels(self, raw, method="correlation"):
        """检测坏通道"""
        # 简化实现，实际应根据method参数使用不同的检测方法
        if method == "correlation":
            # 使用相关性方法检测坏通道
            from mne.preprocessing import find_bad_channels_maxwell
            bads, _ = find_bad_channels_maxwell(raw, cross_talk=None, calibration=None)
            return bads
        else:
            return []
    
    def _run_ica(self, raw, n_components=None, method="fastica"):
        """运行ICA分析"""
        from mne.preprocessing import ICA
        
        # 确定组件数量
        if n_components is None:
            n_components = min(15, len(raw.ch_names) - 1)  # 默认使用15个组件或通道数-1
            
        # 创建ICA对象
        ica = ICA(n_components=n_components, method=method, random_state=42)
        
        # 拟合ICA
        ica.fit(raw)
        
        return ica
    
    def _find_eog_artifacts(self, ica, raw):
        """自动检测眨眼伪迹"""
        from mne.preprocessing import find_eog_events
        
        # 查找EOG事件
        eog_events = find_eog_events(raw)
        
        # 查找与EOG相关的ICA组件
        eog_indices, _ = ica.find_bads_eog(raw, eog_events)
        
        return eog_indices 