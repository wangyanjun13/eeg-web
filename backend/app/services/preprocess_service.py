from pathlib import Path
import numpy as np
from app.models.data_preprocess import FilterParams, ICAParams, ArtifactParams, PreprocessedData, PreprocessParams, SegmentParams, BadSegmentParams, ResampleParams
from scipy import signal
from app.models.data_dataset import RawEEGData
from mne.preprocessing import ICA
import mne
from typing import Dict, List, Optional, Tuple, Union
import time

# 导入Redis缓存功能
from app.core.config import get_preprocess_cache_key
from app.core.redis import save_to_cache, get_from_cache, save_metadata, get_metadata

class PreprocessService:
    def __init__(self, dataset_service):
        self.dataset_service = dataset_service
        # 不依赖AnalysisService，避免循环依赖

    def apply_filter(self, dataset_id: str, subject_id: str, params: FilterParams, channels: List[str] = None) -> RawEEGData:
        """应用滤波器"""
        try:
            # 检查缓存中是否有结果
            cache_key = get_preprocess_cache_key(dataset_id, subject_id, "filter")
            cache_meta_key = f"{cache_key}:meta"
            
            # 首先检查元数据，比对参数判断缓存是否有效
            cached_meta = get_metadata(cache_meta_key)
            if cached_meta:
                # 检查参数是否匹配
                params_dict = params.dict()
                if channels:
                    params_dict['channels'] = channels
                    
                # 参数一致则返回缓存的结果
                if cached_meta.get('params') == params_dict:
                    print(f"找到有效的滤波缓存: {cache_key}")
                    cached_data = get_from_cache(cache_key)
                    if cached_data:
                        return cached_data

            # 缓存无效或不存在，执行滤波处理
            print(f"没有找到有效的缓存，执行滤波处理...")
            start_time = time.time()
            
            # 获取原始数据
            raw_data = self.dataset_service.get_subject_data(dataset_id, subject_id)
            
            if isinstance(raw_data, RawEEGData) and hasattr(raw_data, 'error') and raw_data.error:
                raise ValueError(raw_data.error)

            # 确保数据是有效的
            if not raw_data or not raw_data.data or not raw_data.channels:
                raise ValueError(f"无法获取有效的EEG数据: dataset_id={dataset_id}, subject_id={subject_id}")

            # 设置要处理的通道
            process_channels = channels if channels else raw_data.channels
            
            # 设置滤波参数
            nyquist = raw_data.sampling_rate / 2
            filtered_data = {}
            
            for channel, signal_data in raw_data.data.items():
                # 如果指定了通道列表，只处理列表中的通道
                if channels and channel not in channels:
                    filtered_data[channel] = signal_data
                    continue
                    
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

            result = RawEEGData(
                data=filtered_data,
                times=raw_data.times,
                channels=raw_data.channels,
                duration=raw_data.duration,
                sampling_rate=raw_data.sampling_rate,
                dataset_id=dataset_id,
                subject_id=subject_id
            )
            
            # 计算处理时间
            process_time = time.time() - start_time
            print(f"滤波处理完成，耗时: {process_time:.2f}秒")
            
            # 缓存处理结果
            params_dict = params.dict()
            if channels:
                params_dict['channels'] = channels
                
            metadata = {
                'params': params_dict,
                'process_time': process_time,
                'timestamp': time.time()
            }
            
            save_metadata(cache_meta_key, metadata)
            save_to_cache(cache_key, result)
            print(f"已缓存滤波结果: {cache_key}")
            
            return result
        except Exception as e:
            error_msg = f"滤波处理失败: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)

    def run_ica(self, dataset_id: str, subject_id: str, params: ICAParams) -> RawEEGData:
        """运行ICA分析"""
        # 检查缓存
        cache_key = get_preprocess_cache_key(dataset_id, subject_id, "ica")
        cache_meta_key = f"{cache_key}:meta"
        
        cached_meta = get_metadata(cache_meta_key)
        if cached_meta and cached_meta.get('params') == params.dict():
            cached_data = get_from_cache(cache_key)
            if cached_data:
                print(f"使用缓存的ICA结果: {cache_key}")
                return cached_data
                
        # 没有缓存，执行处理
        start_time = time.time()
        # 获取原始数据
        raw_data = self.dataset_service.get_subject_data(dataset_id, subject_id)
        
        # 转换为numpy数组
        data = np.array([raw_data.data[ch] for ch in raw_data.channels])
        
        # 运行ICA
        ica = ICA(
            n_components=params.n_components,
            random_state=42
        )
        ica.fit(data)
        
        # 应用ICA
        cleaned_data = ica.apply(data)
        
        # 转换回字典格式
        processed_data = {
            ch: cleaned_data[i].tolist()
            for i, ch in enumerate(raw_data.channels)
        }
        
        result = RawEEGData(
            data=processed_data,
            times=raw_data.times,
            channels=raw_data.channels,
            duration=raw_data.duration,
            sampling_rate=raw_data.sampling_rate,
            dataset_id=dataset_id,
            subject_id=subject_id
        )
        
        # 计算处理时间并缓存结果
        process_time = time.time() - start_time
        metadata = {
            'params': params.dict(),
            'process_time': process_time,
            'timestamp': time.time()
        }
        
        save_metadata(cache_meta_key, metadata)
        save_to_cache(cache_key, result)
        
        return result

    def remove_artifacts(self, dataset_id: str, subject_id: str, params: ArtifactParams) -> RawEEGData:
        """去除伪迹"""
        # 检查缓存
        cache_key = get_preprocess_cache_key(dataset_id, subject_id, "artifacts")
        cache_meta_key = f"{cache_key}:meta"
        
        cached_meta = get_metadata(cache_meta_key)
        if cached_meta and cached_meta.get('params') == params.dict():
            cached_data = get_from_cache(cache_key)
            if cached_data:
                print(f"使用缓存的伪迹处理结果: {cache_key}")
                return cached_data
        
        # 没有缓存，执行处理
        start_time = time.time()
        # 获取原始数据
        raw_data = self.dataset_service.get_subject_data(dataset_id, subject_id)
        
        if isinstance(raw_data, RawEEGData) and hasattr(raw_data, 'error') and raw_data.error:
            raise ValueError(raw_data.error)
        
        # 转换为numpy数组以便处理
        data_array = np.array([raw_data.data[ch] for ch in raw_data.channels])
        
        # 简单的阈值去伪迹方法
        if params.amplitude_threshold and params.amplitude_threshold > 0:
            # 计算每个通道的标准差
            channel_stds = np.std(data_array, axis=1)
            
            # 对每个通道应用阈值
            for i, ch in enumerate(raw_data.channels):
                # 获取当前通道数据
                channel_data = data_array[i]
                
                # 计算阈值（标准差的倍数）
                threshold = channel_stds[i] * params.amplitude_threshold
                
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
        
        result = RawEEGData(
            data=processed_data,
            times=raw_data.times,
            channels=raw_data.channels,
            duration=raw_data.duration,
            sampling_rate=raw_data.sampling_rate,
            dataset_id=dataset_id,
            subject_id=subject_id
        )
        
        # 计算处理时间并缓存结果
        process_time = time.time() - start_time
        metadata = {
            'params': params.dict(),
            'process_time': process_time,
            'timestamp': time.time()
        }
        
        save_metadata(cache_meta_key, metadata)
        save_to_cache(cache_key, result)
        
        return result
    
    def preprocess_eeg(self, raw, params: Optional[PreprocessParams] = None):
        # 使用默认参数或用户提供的参数
        if params is None:
            params = PreprocessParams.get_template("default")
            
        # 记录应用的处理方法
        applied_methods = []
            
        # 按顺序应用预处理步骤
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

    def segment_data(self, dataset_id: str, subject_id: str, params: SegmentParams) -> RawEEGData:
        """对数据进行分段处理"""
        try:
            # 获取输入数据
            input_data = self.get_input_data_for_step(dataset_id, subject_id, "segment")
            
            # 如果没有输入数据，使用原始数据
            if not input_data:
                print(f"未找到预处理链中的数据，获取原始数据")
                input_data = self.dataset_service.get_subject_data(
                    dataset_id, 
                    subject_id,
                    0 if params.use_original_full_data else params.start_time,
                    None if params.use_original_full_data else (params.end_time - params.start_time)
                )
            
            # 提取基本数据 - 增加健壮性检查
            data = {}
            for ch in input_data.channels:
                if ch in input_data.data:
                    data[ch] = input_data.data[ch]
                    
            times = input_data.times
            channels = input_data.channels
            sampling_rate = input_data.sampling_rate
            
            # 数据验证
            if not data or not times or not channels:
                raise ValueError("输入数据缺少必要信息")
            
            # 确保数据中不包含非标准浮点值
            for channel in data:
                channel_data = data[channel]
                for i, value in enumerate(channel_data):
                    if np.isnan(value) or np.isinf(value):
                        # 将非标准浮点值替换为0
                        channel_data[i] = 0.0
            
            # 根据分段模式进行不同的处理
            if params.segment_mode == "time":
                # 简化时间窗口分段
                result = self._segment_by_time_window(
                    data, times, channels, sampling_rate,
                    params.start_time, params.end_time,
                    params.use_original_full_data,
                    dataset_id, subject_id
                )
            elif params.segment_mode == "eeglab":
                # 简化EEGLAB风格分段
                result = self._segment_eeglab_style(
                    data, times, channels, sampling_rate,
                    params.segment_length, params.segment_overlap / 100,
                    params.remove_incomplete,
                    dataset_id, subject_id
                )
            elif params.segment_mode == "event":
                # 简化事件相关分段
                events = self._get_events(dataset_id, subject_id)
                if not events or len(events) == 0:
                    # 如果没有事件，回退到时间窗口分段
                    print("警告: 未找到事件数据，回退到时间窗口分段")
                    result = self._segment_by_time_window(
                        data, times, channels, sampling_rate,
                        params.start_time, params.end_time, 
                        params.use_original_full_data,
                        dataset_id, subject_id
                    )
                else:
                    result = self._segment_by_events(
                        data, times, channels, sampling_rate,
                        events, params.event_id,
                        params.pre_event, params.post_event,
                        dataset_id, subject_id
                    )
            else:
                raise ValueError(f"未知的分段模式: {params.segment_mode}")
            
            # 应用基线校正（如果需要）
            if params.apply_baseline:
                result = self._apply_baseline_correction(
                    result, params.baseline_start, params.baseline_end
                )
            
            # 确保结果中包含dataset_id和subject_id
            if not hasattr(result, 'dataset_id') or result.dataset_id is None:
                result.dataset_id = dataset_id
            if not hasattr(result, 'subject_id') or result.subject_id is None:
                result.subject_id = subject_id
            
            return result
        except Exception as e:
            import traceback
            print(f"分段处理失败: {str(e)}")
            print(traceback.format_exc())
            raise ValueError(f"分段处理失败: {str(e)}")

    def _segment_by_time_window(self, data, times, channels, sampling_rate, start_time, end_time, use_full_data=False, dataset_id=None, subject_id=None):
        """根据时间窗口进行分段 - 简化版"""
        try:
            # 如果使用完整数据，直接返回
            if use_full_data:
                return RawEEGData(
                    data=data,
                    times=times,
                    channels=channels,
                    duration=times[-1] - times[0] if len(times) > 0 else 0,
                    sampling_rate=sampling_rate,
                    dataset_id=dataset_id,
                    subject_id=subject_id,
                    segment_info={"type": "full_data"}
                )
            
            # 防御性编程：确保时间数组不为空
            if not times or len(times) == 0:
                raise ValueError("时间点数组为空")
            
            # 查找开始和结束索引 - 简化逻辑
            start_idx = 0
            for i, t in enumerate(times):
                if t >= start_time:
                    start_idx = i
                    break
            
            end_idx = len(times)
            for i, t in enumerate(times[start_idx:], start_idx):
                if t >= end_time:
                    end_idx = i
                    break
            
            # 安全检查：确保索引有效
            if start_idx >= len(times):
                start_idx = 0
            if end_idx > len(times):
                end_idx = len(times)
            if start_idx >= end_idx:
                # 至少保留一个数据点
                if start_idx < len(times) - 1:
                    end_idx = start_idx + 1
                else:
                    start_idx = max(0, len(times) - 2)
                    end_idx = len(times) - 1
            
            # 提取数据片段
            segment_data = {}
            segment_times = times[start_idx:end_idx]
            
            for channel in channels:
                if channel in data:
                    if len(data[channel]) > start_idx:
                        channel_slice = data[channel][start_idx:min(end_idx, len(data[channel]))]
                        # 确保切片不为空
                        if not channel_slice:
                            # 如果切片为空，创建与时间点等长的零数组
                            segment_data[channel] = [0.0] * len(segment_times)
                        else:
                            segment_data[channel] = channel_slice
                    else:
                        # 如果通道数据不足，创建零填充数组
                        segment_data[channel] = [0.0] * len(segment_times)
                else:
                    # 通道不存在，创建零填充数组
                    segment_data[channel] = [0.0] * len(segment_times)
            
            # 创建结果对象
            return RawEEGData(
                data=segment_data,
                times=segment_times,
                channels=channels,
                duration=segment_times[-1] - segment_times[0] if len(segment_times) > 0 else 0,
                sampling_rate=sampling_rate,
                dataset_id=dataset_id,
                subject_id=subject_id,
                segment_info={"type": "time_window", "start": start_time, "end": end_time}
            )
        except Exception as e:
            print(f"时间窗口分段错误: {str(e)}")
            # 发生错误时返回一个最小的有效数据结构
            # 创建一个最小的数据结构以避免前端渲染错误
            min_segment_data = {ch: [0.0] for ch in channels}
            min_segment_times = [0.0]
            
            return RawEEGData(
                data=min_segment_data,
                times=min_segment_times,
                channels=channels,
                duration=0.0,
                sampling_rate=sampling_rate,
                dataset_id=dataset_id,
                subject_id=subject_id,
                segment_info={"type": "time_window", "start": start_time, "end": end_time, "error": str(e)}
            )

    def _segment_eeglab_style(self, data, times, channels, sampling_rate, segment_length, overlap_ratio, remove_incomplete, dataset_id=None, subject_id=None):
        """EEGLAB风格分段 - 简化版"""
        # 参数验证
        if segment_length <= 0:
            raise ValueError("段长度必须大于0")
        
        # 防御性编程：确保时间数组不为空
        if not times or len(times) == 0:
            raise ValueError("时间点数组为空")
        
        # 计算需要的样本点数
        points_per_segment = int(segment_length * sampling_rate)
        overlap_points = int(points_per_segment * overlap_ratio)
        step_size = max(1, points_per_segment - overlap_points)  # 确保步长至少为1
        
        # 简化为只取第一个段
        start_idx = 0
        end_idx = min(start_idx + points_per_segment, len(times))
        
        # 提取数据片段
        segment_data = {}
        segment_times = times[start_idx:end_idx]
        
        for channel in channels:
            if channel in data:
                if len(data[channel]) >= end_idx:
                    segment_data[channel] = data[channel][start_idx:end_idx]
                else:
                    # 如果通道数据不足，截断到可用长度
                    available_length = min(end_idx, len(data[channel]))
                    segment_data[channel] = data[channel][start_idx:available_length]
                    # 如果需要，可以用零填充剩余部分
                    if available_length < end_idx:
                        segment_data[channel].extend([0.0] * (end_idx - available_length))
        
        # 计算总段数（仅用于信息显示）
        total_samples = len(times)
        segment_count = (total_samples - points_per_segment) // step_size + 1
        if segment_count <= 0:
            segment_count = 1
        
        # 创建结果
        return RawEEGData(
            data=segment_data,
            times=segment_times,
            channels=channels,
            duration=segment_times[-1] - segment_times[0] if len(segment_times) > 0 else 0,
            sampling_rate=sampling_rate,
            dataset_id=dataset_id,
            subject_id=subject_id,
            segment_info={
                "type": "eeglab_style", 
                "segment_length": segment_length,
                "overlap_ratio": overlap_ratio,
                "total_segments": segment_count
            }
        )

    def _segment_by_events(self, data, times, channels, sampling_rate, events, event_id, pre_event, post_event, dataset_id=None, subject_id=None):
        """根据事件进行分段 - 简化版"""
        # 参数验证
        if not events:
            raise ValueError("没有可用的事件数据")
        
        # 防御性编程：确保时间数组不为空
        if not times or len(times) == 0:
            raise ValueError("时间点数组为空")
        
        # 查找匹配的事件
        matching_events = []
        for event in events:
            if str(event.get('id', '')).strip() == str(event_id).strip() or str(event.get('name', '')).strip() == str(event_id).strip():
                matching_events.append(event)
        
        # 如果没有匹配的事件，使用第一个事件
        if not matching_events and events:
            matching_events = [events[0]]
        
        # 如果仍然没有事件，抛出异常
        if not matching_events:
            raise ValueError("没有可用的事件数据")
        
        # 使用第一个匹配的事件
        event = matching_events[0]
        event_time = float(event.get('onset', 0))
        
        # 计算时间窗口
        start_time = event_time - pre_event
        end_time = event_time + post_event
        
        # 查找索引
        start_idx = 0
        for i, t in enumerate(times):
            if t >= start_time:
                start_idx = i
                break
        
        end_idx = len(times)
        for i, t in enumerate(times[start_idx:], start_idx):
            if t >= end_time:
                end_idx = i
                break
        
        # 安全检查：确保索引有效
        if start_idx >= len(times):
            start_idx = 0
        if end_idx > len(times):
            end_idx = len(times)
        if start_idx >= end_idx:
            # 至少保留一个数据点
            if start_idx < len(times) - 1:
                end_idx = start_idx + 1
            else:
                start_idx = max(0, len(times) - 2)
                end_idx = len(times) - 1
        
        # 提取数据片段
        segment_data = {}
        segment_times = times[start_idx:end_idx]
        
        # 调整时间点相对于事件发生时间
        adjusted_times = [t - event_time for t in segment_times]
        
        for channel in channels:
            if channel in data:
                if len(data[channel]) > start_idx:
                    segment_data[channel] = data[channel][start_idx:min(end_idx, len(data[channel]))]
                else:
                    # 如果通道数据不足，使用空数组
                    segment_data[channel] = []
        
        # 创建结果
        return RawEEGData(
            data=segment_data,
            times=adjusted_times,  # 使用调整后的时间
            channels=channels,
            duration=adjusted_times[-1] - adjusted_times[0] if len(adjusted_times) > 0 else 0,
            sampling_rate=sampling_rate,
            dataset_id=dataset_id,
            subject_id=subject_id,
            segment_info={
                "type": "event_related",
                "event_id": event_id,
                "event_time": event_time,
                "pre_event": pre_event,
                "post_event": post_event
            }
        )

    def _sanitize_float_array(self, arr):
        """清理数组中的非标准浮点数"""
        import numpy as np
        # 将NaN替换为0，将无穷值替换为极大/极小值
        if isinstance(arr, np.ndarray):
            sanitized = np.array(arr, dtype=np.float64)
            # 替换NaN
            sanitized[np.isnan(sanitized)] = 0.0
            # 替换正无穷
            sanitized[np.isposinf(sanitized)] = np.finfo(np.float64).max
            # 替换负无穷
            sanitized[np.isneginf(sanitized)] = np.finfo(np.float64).min
            return sanitized
        return arr

    def _apply_baseline_correction(self, raw_data: RawEEGData, start: float, end: float) -> RawEEGData:
        """应用基线校正"""
        try:
            # 转换为numpy数组进行处理
            data_dict = raw_data.data
            times = raw_data.times
            
            # 处理空时间数组
            if not times:
                print("警告: 基线校正 - 时间点数组为空，跳过校正")
                return raw_data
            
            # 找到基线范围的索引
            try:
                start_idx = np.where(np.array(times) >= start)[0][0] if start > times[0] else 0
            except IndexError:
                # 如果找不到，使用第一个点
                start_idx = 0
            
            try:
                end_idx = np.where(np.array(times) <= end)[0][-1] if end < times[-1] else len(times) - 1
            except IndexError:
                # 如果找不到，使用最后一个点
                end_idx = len(times) - 1
            
            # 确保索引有效
            if start_idx >= len(times):
                start_idx = 0
            if end_idx >= len(times):
                end_idx = len(times) - 1
            if start_idx > end_idx:
                start_idx, end_idx = end_idx, start_idx
            
            # 对每个通道应用基线校正
            for channel in data_dict.keys():
                try:
                    channel_data = np.array(data_dict[channel])
                    # 确保索引范围在channel_data长度内
                    valid_end_idx = min(end_idx, len(channel_data) - 1)
                    valid_start_idx = min(start_idx, valid_end_idx)
                    
                    if valid_end_idx >= valid_start_idx:
                        baseline_mean = np.mean(channel_data[valid_start_idx:valid_end_idx+1])
                        channel_data = channel_data - baseline_mean
                        data_dict[channel] = channel_data.tolist()
                except Exception as channel_error:
                    print(f"警告: 通道 {channel} 基线校正失败: {str(channel_error)}")
            
            # 创建新的RawEEGData对象
            segment_info = raw_data.segment_info.copy() if raw_data.segment_info else {}
            segment_info["baseline_corrected"] = True
            segment_info["baseline_start"] = start
            segment_info["baseline_end"] = end
            
            result = RawEEGData(
                data=data_dict,
                times=times,
                channels=raw_data.channels,
                duration=raw_data.duration,
                sampling_rate=raw_data.sampling_rate,
                dataset_id=raw_data.dataset_id,
                subject_id=raw_data.subject_id,
                segment_info=segment_info
            )
            
            return result
            
        except Exception as e:
            print(f"基线校正错误: {str(e)}")
            # 如果基线校正失败，返回原始数据
            return raw_data

    def _get_events(self, dataset_id: str, subject_id: str):
        """获取事件信息"""
        try:
            # 从数据集服务获取事件信息
            events_info = self.dataset_service.get_events_info(dataset_id, subject_id)
            return events_info.get("events", [])
        except Exception as e:
            print(f"获取事件信息失败: {str(e)}")
            # 返回空列表而不是抛出异常
            return []

    def detect_bad_segments(self, dataset_id: str, subject_id: str, params: BadSegmentParams) -> RawEEGData:
        """检测并剔除坏段"""
        try:
            # 检查缓存
            cache_key = get_preprocess_cache_key(dataset_id, subject_id, "bad_segments")
            cache_meta_key = f"{cache_key}:meta"
            
            # 首先检查元数据，比对参数判断缓存是否有效
            cached_meta = get_metadata(cache_meta_key)
            if cached_meta:
                # 检查参数是否匹配
                params_dict = params.dict()
                
                # 参数一致则返回缓存的结果
                if cached_meta.get('params') == params_dict:
                    print(f"找到有效的坏段处理缓存: {cache_key}")
                    cached_data = get_from_cache(cache_key)
                    if cached_data:
                        return cached_data

            # 缓存无效或不存在，执行坏段处理
            print(f"没有找到有效的缓存，执行坏段处理...")
            start_time = time.time()
            
            # 获取输入数据（前一步的结果）
            input_data = self.get_input_data_for_step(dataset_id, subject_id, "bad_segments")
            
            if isinstance(input_data, RawEEGData) and hasattr(input_data, 'error') and input_data.error:
                raise ValueError(input_data.error)

            # 坏段检测逻辑
            bad_segments = []
            
            if params.detection_method == "auto":
                # 自动检测坏段 - 结合多种方法
                # 1. 检测振幅超限
                bad_segments.extend(self._detect_amplitude_violations(input_data, params.amplitude_threshold))
                
                # 2. 检测梯度超限
                bad_segments.extend(self._detect_gradient_violations(input_data, params.gradient_threshold))
                
                # 合并重叠的坏段
                bad_segments = self._merge_overlapping_segments(bad_segments)
            
            elif params.detection_method == "threshold":
                # 仅使用阈值检测坏段
                bad_segments = self._detect_amplitude_violations(input_data, params.amplitude_threshold)
            
            elif params.detection_method == "manual":
                # 手动标记的坏段 - 此处应从请求或数据库中获取
                # 简化处理，假设已经有预先标记的坏段
                bad_segments = []
            else:
                raise ValueError(f"不支持的坏段检测方法: {params.detection_method}")
            
            # 应用坏段剔除
            processed_data = {}
            
            if params.reject_method == "zero":
                # 将坏段数据置零
                for channel in input_data.channels:
                    channel_data = list(input_data.data[channel])
                    
                    for segment in bad_segments:
                        start_sample = int(segment["start"] * input_data.sampling_rate)
                        end_sample = int(segment["end"] * input_data.sampling_rate)
                        
                        # 确保索引有效
                        if start_sample < 0:
                            start_sample = 0
                        if end_sample > len(channel_data):
                            end_sample = len(channel_data)
                        
                        # 将坏段置零
                        for i in range(start_sample, end_sample):
                            channel_data[i] = 0.0
                    
                    processed_data[channel] = channel_data
                
            elif params.reject_method == "interpolate":
                # 对坏段进行插值
                for channel in input_data.channels:
                    channel_data = list(input_data.data[channel])
                    
                    for segment in bad_segments:
                        start_sample = int(segment["start"] * input_data.sampling_rate)
                        end_sample = int(segment["end"] * input_data.sampling_rate)
                        
                        # 确保索引有效
                        if start_sample < 0:
                            start_sample = 0
                        if end_sample > len(channel_data):
                            end_sample = len(channel_data)
                        
                        if start_sample > 0 and end_sample < len(channel_data):
                            # 使用线性插值
                            start_value = channel_data[start_sample - 1]
                            end_value = channel_data[end_sample]
                            segment_length = end_sample - start_sample
                            
                            for i in range(segment_length):
                                t = i / segment_length
                                interpolated_value = start_value * (1 - t) + end_value * t
                                channel_data[start_sample + i] = interpolated_value
                    
                    processed_data[channel] = channel_data
                
            elif params.reject_method == "remove":
                # 移除坏段 (注意：这会改变数据长度)
                # 简化处理：仅支持移除连续的单个坏段
                if len(bad_segments) == 1:
                    segment = bad_segments[0]
                    start_sample = int(segment["start"] * input_data.sampling_rate)
                    end_sample = int(segment["end"] * input_data.sampling_rate)
                    
                    # 确保索引有效
                    if start_sample < 0:
                        start_sample = 0
                    if end_sample > len(input_data.times):
                        end_sample = len(input_data.times)
                    
                    # 移除坏段
                    times = input_data.times[:start_sample] + input_data.times[end_sample:]
                    
                    for channel in input_data.channels:
                        channel_data = input_data.data[channel]
                        processed_data[channel] = channel_data[:start_sample] + channel_data[end_sample:]
                else:
                    raise ValueError("移除方法只支持单个连续的坏段")
            else:
                raise ValueError(f"不支持的坏段剔除方法: {params.reject_method}")
            
            # 创建结果数据
            result = RawEEGData(
                data=processed_data,
                times=input_data.times,  # 如果使用remove方法，这里需要相应修改
                channels=input_data.channels,
                duration=input_data.duration,
                sampling_rate=input_data.sampling_rate,
                dataset_id=dataset_id,
                subject_id=subject_id,
                bad_segments=bad_segments
            )
            
            # 计算处理时间
            process_time = time.time() - start_time
            print(f"坏段处理完成，耗时: {process_time:.2f}秒")
            
            # 缓存处理结果
            params_dict = params.dict()
            metadata = {
                'params': params_dict,
                'process_time': process_time,
                'timestamp': time.time()
            }
            
            save_metadata(cache_meta_key, metadata)
            save_to_cache(cache_key, result)
            print(f"已缓存坏段处理结果: {cache_key}")
            
            return result
        except Exception as e:
            error_msg = f"坏段处理失败: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)

    # 辅助方法

    def _detect_amplitude_violations(self, data, threshold):
        """检测振幅超过阈值的坏段"""
        bad_segments = []
        
        # 简化实现，实际应用可能需要更复杂的算法
        for channel in data.channels:
            channel_data = data.data[channel]
            
            # 检测连续超过阈值的区域
            in_bad_segment = False
            start_sample = 0
            
            for i, value in enumerate(channel_data):
                if abs(value) > threshold:
                    if not in_bad_segment:
                        in_bad_segment = True
                        start_sample = i
                else:
                    if in_bad_segment:
                        in_bad_segment = False
                        end_sample = i
                        
                        # 转换为时间
                        start_time = data.times[start_sample]
                        end_time = data.times[end_sample]
                        
                        # 添加到坏段列表
                        bad_segments.append({
                            "start": start_time,
                            "end": end_time,
                            "channels": [channel],
                            "reason": "振幅超限"
                        })
            
            # 如果数据结束时仍在坏段中
            if in_bad_segment:
                end_sample = len(channel_data) - 1
                start_time = data.times[start_sample]
                end_time = data.times[end_sample]
                
                bad_segments.append({
                    "start": start_time,
                    "end": end_time,
                    "channels": [channel],
                    "reason": "振幅超限"
                })
        
        return bad_segments

    def _detect_gradient_violations(self, data, threshold):
        """检测梯度超过阈值的坏段"""
        bad_segments = []
        
        # 简化实现，实际应用可能需要更复杂的算法
        for channel in data.channels:
            channel_data = data.data[channel]
            
            # 检测连续梯度超过阈值的区域
            in_bad_segment = False
            start_sample = 0
            
            for i in range(1, len(channel_data)):
                gradient = abs(channel_data[i] - channel_data[i-1]) * data.sampling_rate / 1000  # μV/ms
                
                if gradient > threshold:
                    if not in_bad_segment:
                        in_bad_segment = True
                        start_sample = i - 1
                else:
                    if in_bad_segment:
                        in_bad_segment = False
                        end_sample = i + 1  # 多包含一个点
                        
                        # 转换为时间
                        start_time = data.times[start_sample]
                        end_time = data.times[min(end_sample, len(data.times)-1)]
                        
                        # 添加到坏段列表
                        bad_segments.append({
                            "start": start_time,
                            "end": end_time,
                            "channels": [channel],
                            "reason": "梯度超限"
                        })
            
            # 如果数据结束时仍在坏段中
            if in_bad_segment:
                end_sample = len(channel_data) - 1
                start_time = data.times[start_sample]
                end_time = data.times[end_sample]
                
                bad_segments.append({
                    "start": start_time,
                    "end": end_time,
                    "channels": [channel],
                    "reason": "梯度超限"
                })
        
        return bad_segments

    def _merge_overlapping_segments(self, segments):
        """合并重叠的坏段"""
        if not segments:
            return []
        
        # 按起始时间排序
        sorted_segments = sorted(segments, key=lambda s: s["start"])
        
        merged = [sorted_segments[0]]
        
        for current in sorted_segments[1:]:
            previous = merged[-1]
            
            # 检查是否重叠
            if current["start"] <= previous["end"]:
                # 合并段
                previous["end"] = max(previous["end"], current["end"])
                # 合并通道
                previous["channels"] = list(set(previous["channels"] + current["channels"]))
                # 合并原因
                if current["reason"] not in previous["reason"]:
                    previous["reason"] = f"{previous['reason']}, {current['reason']}"
            else:
                # 添加新段
                merged.append(current)
        
        return merged

    def get_input_data_for_step(self, dataset_id: str, subject_id: str, step_name: str) -> Union[Dict, None]:
        """获取处理步骤的输入数据
        
        自动获取上一步的处理结果作为输入，如果没有则获取原始数据
        
        Args:
            dataset_id: 数据集ID
            subject_id: 受试者ID
            step_name: 当前处理步骤
        
        Returns:
            输入数据
        """
        try:
            # 所有处理步骤，按顺序排列
            steps = ["filter", "resample", "segment", "badChannels", "badSegments", "reference", "ica", "artifacts"]
            
            # 找出当前步骤的索引
            current_index = steps.index(step_name) if step_name in steps else -1
            
            # 如果是第一步或找不到步骤，返回原始数据
            if current_index <= 0:
                return self.dataset_service.get_subject_data(dataset_id, subject_id)
            
            # 获取前一步的结果作为输入
            prev_step = steps[current_index - 1]
            cache_key = get_preprocess_cache_key(dataset_id, subject_id, prev_step)
            input_data = get_from_cache(cache_key)
            
            # 如果找不到前一步的结果，尝试更前面的步骤
            if not input_data:
                for i in range(current_index - 2, -1, -1):
                    prev_step = steps[i]
                    cache_key = get_preprocess_cache_key(dataset_id, subject_id, prev_step)
                    input_data = get_from_cache(cache_key)
                    if input_data:
                        break
            
            # 如果仍然找不到，使用原始数据
            if not input_data:
                input_data = self.dataset_service.get_subject_data(dataset_id, subject_id)
            
            return input_data
        except Exception as e:
            print(f"获取步骤输入数据失败: {str(e)}")
            # 发生错误时返回原始数据
            return self.dataset_service.get_subject_data(dataset_id, subject_id)

    def apply_resample(self, dataset_id: str, subject_id: str, params: ResampleParams, channels: List[str] = None) -> RawEEGData:
        """应用重采样处理，使用与EEGLAB类似的多相滤波器方法"""
        try:
            # 检查缓存
            cache_key = get_preprocess_cache_key(dataset_id, subject_id, "resample")
            cache_meta_key = f"{cache_key}:meta"
            
            # 首先检查元数据，比对参数判断缓存是否有效
            cached_meta = get_metadata(cache_meta_key)
            if cached_meta:
                # 检查参数是否匹配
                params_dict = params.dict()
                if channels:
                    params_dict['channels'] = channels
                    
                # 参数一致则返回缓存的结果
                if cached_meta.get('params') == params_dict:
                    print(f"找到有效的重采样缓存: {cache_key}")
                    cached_data = get_from_cache(cache_key)
                    if cached_data:
                        return cached_data

            # 缓存无效或不存在，执行重采样处理
            print(f"执行重采样处理: {params.resample_freq}Hz")
            start_time = time.time()
            
            # 获取输入数据（必须是滤波后的数据）
            input_data = self.get_input_data_for_step(dataset_id, subject_id, "resample")
            
            if not input_data:
                raise ValueError("无法获取输入数据")
            
            if not params.resample or params.resample_freq <= 0:
                return input_data
            
            # 获取原始采样率和目标采样率
            orig_freq = input_data.sampling_rate
            target_freq = params.resample_freq
            
            # 如果原始采样率和目标采样率几乎相同，直接返回原始数据
            if abs(orig_freq - target_freq) < 0.01:
                print(f"原始采样率({orig_freq}Hz)和目标采样率({target_freq}Hz)几乎相同，跳过重采样")
                return input_data
            
            # 为每个通道应用重采样
            resampled_data = {}
            process_channels = channels if channels else input_data.channels
            
            # 计算最优多项式分子/分母比例
            def gcd(a, b):
                while b:
                    a, b = b, a % b
                return a
            
            up = int(target_freq)
            down = int(orig_freq)
            g = gcd(up, down)
            up = up // g
            down = down // g

            for channel in input_data.channels:
                # 跳过不需要处理的通道
                if channels and channel not in channels:
                    resampled_data[channel] = input_data.data[channel]
                    continue
                
                # 获取通道数据
                signal_data = np.array(input_data.data[channel])
                
                if len(signal_data) == 0:
                    resampled_data[channel] = []
                    continue
                    
                # 使用resample_poly进行重采样 - 多相滤波方法，与EEGLAB类似
                try:
                    # 针对不同情况优化窗口参数
                    if target_freq < orig_freq:
                        # 降采样 - 使用较温和的窗口保留更多细节
                        window = ('kaiser', 3.0)
                    else:
                        # 升采样
                        window = ('kaiser', 5.0)
                        
                    # 执行多相重采样
                    resampled_signal = signal.resample_poly(signal_data, up, down, window=window)
                    resampled_data[channel] = resampled_signal.tolist()
                except Exception as e:
                    print(f"通道 {channel} 重采样失败: {str(e)}，使用备用方法")
                    # 备用方法
                    num_samples = int(len(signal_data) * target_freq / orig_freq)
                    resampled_signal = signal.resample(signal_data, num_samples)
                    resampled_data[channel] = resampled_signal.tolist()
                
            # 重新计算时间点 - 关键修复
            if len(list(resampled_data.values())[0]) > 0:
                n_samples = len(list(resampled_data.values())[0])
                orig_duration = input_data.duration
                
                # 使用新采样率生成时间点
                resampled_times = np.arange(0, n_samples) / target_freq
                
                # 截断超出原始持续时间的部分
                if resampled_times[-1] > orig_duration:
                    cutoff_index = np.searchsorted(resampled_times, orig_duration, side='right')
                    resampled_times = resampled_times[:cutoff_index]
                    # 同时截断数据
                    for channel in resampled_data:
                        resampled_data[channel] = resampled_data[channel][:cutoff_index]
                    n_samples = len(resampled_times)
                
                # 转换为列表
                resampled_times = resampled_times.tolist()
                
                # 创建结果数据
                result = RawEEGData(
                    data=resampled_data,
                    times=resampled_times,
                    channels=input_data.channels,
                    duration=resampled_times[-1] if resampled_times else orig_duration,
                    sampling_rate=params.resample_freq,
                    dataset_id=dataset_id,
                    subject_id=subject_id
                )
            else:
                # 如果没有有效数据，返回原始数据
                return input_data
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 缓存处理结果
            params_dict = params.dict()
            if channels:
                params_dict['channels'] = channels
                
            metadata = {
                'params': params_dict,
                'process_time': process_time,
                'timestamp': time.time()
            }
            
            save_metadata(cache_meta_key, metadata)
            save_to_cache(cache_key, result)
            print(f"重采样完成，用时:{process_time:.2f}秒")
            
            return result
        except Exception as e:
            error_msg = f"重采样处理失败: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)