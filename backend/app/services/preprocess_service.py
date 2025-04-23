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
        """数据分段处理"""
        try:
            # 检查缓存
            cache_key = get_preprocess_cache_key(dataset_id, subject_id, "segment")
            cache_meta_key = f"{cache_key}:meta"
            
            # 首先检查元数据，比对参数判断缓存是否有效
            cached_meta = get_metadata(cache_meta_key)
            if cached_meta:
                # 检查参数是否匹配
                params_dict = params.dict()
                
                # 参数一致则返回缓存的结果
                if cached_meta.get('params') == params_dict:
                    print(f"找到有效的分段缓存: {cache_key}")
                    cached_data = get_from_cache(cache_key)
                    if cached_data:
                        return cached_data

            # 缓存无效或不存在，执行分段处理
            print(f"没有找到有效的缓存，执行分段处理...")
            start_time = time.time()
            
            # 获取输入数据（前一步的结果）
            input_data = self.get_input_data_for_step(dataset_id, subject_id, "segment")
            
            if isinstance(input_data, RawEEGData) and hasattr(input_data, 'error') and input_data.error:
                raise ValueError(input_data.error)

            # 实际分段处理逻辑
            if params.segment_mode == "time":
                # 时间窗口分段
                start_sample = max(0, int(params.start_time * input_data.sampling_rate))
                end_sample = min(len(input_data.times), int(params.end_time * input_data.sampling_rate))
                
                # 获取时间数据，确保是列表
                if isinstance(input_data.times, np.ndarray):
                    segmented_times = input_data.times[start_sample:end_sample].tolist()
                else:
                    segmented_times = input_data.times[start_sample:end_sample]
                
                # 提取分段数据
                segmented_data = {}
                for channel in input_data.channels:
                    # 获取通道数据，确保是列表
                    if isinstance(input_data.data[channel], np.ndarray):
                        segmented_data[channel] = input_data.data[channel][start_sample:end_sample].tolist()
                    else:
                        segmented_data[channel] = input_data.data[channel][start_sample:end_sample]
                
                # 基线校正
                if params.apply_baseline:
                    baseline_start_idx = int((params.baseline_start + params.start_time) * input_data.sampling_rate)
                    baseline_end_idx = int((params.baseline_end + params.start_time) * input_data.sampling_rate)
                    
                    if baseline_start_idx >= 0 and baseline_end_idx <= len(segmented_times):
                        # 对每个通道应用基线校正
                        for channel in input_data.channels:
                            baseline = np.mean(segmented_data[channel][baseline_start_idx:baseline_end_idx])
                            segmented_data[channel] = [val - baseline for val in segmented_data[channel]]
                
                # 创建结果数据
                result = RawEEGData(
                    data=segmented_data,
                    times=segmented_times,
                    channels=input_data.channels,
                    duration=params.end_time - params.start_time,
                    sampling_rate=input_data.sampling_rate,
                    dataset_id=dataset_id,
                    subject_id=subject_id,
                    segment_info={
                        "mode": "time",
                        "start": params.start_time,
                        "end": params.end_time,
                        "baseline": {
                            "applied": params.apply_baseline,
                            "start": params.baseline_start,
                            "end": params.baseline_end
                        }
                    }
                )
            
            elif params.segment_mode == "event":
                # 事件相关分段
                events = input_data.events or []
                target_events = [e for e in events if e.name == params.event_name]
                
                if not target_events:
                    raise ValueError(f"未找到名为 '{params.event_name}' 的事件")
                
                # 创建分段集合
                segmented_datasets = []
                
                for event in target_events:
                    event_time = event.time
                    
                    # 计算分段起止时间
                    segment_start = event_time - params.pre_event
                    segment_end = event_time + params.post_event
                    
                    # 确保分段在有效范围内
                    if segment_start < 0:
                        segment_start = 0
                    if segment_end > input_data.duration:
                        segment_end = input_data.duration
                    
                    # 转换为采样点索引
                    start_sample = int(segment_start * input_data.sampling_rate)
                    end_sample = int(segment_end * input_data.sampling_rate)
                    
                    # 提取分段数据
                    segment_data = {}
                    segment_times = input_data.times[start_sample:end_sample]
                    
                    for channel in input_data.channels:
                        segment_data[channel] = input_data.data[channel][start_sample:end_sample]
                    
                    # 基线校正
                    if params.apply_baseline:
                        # 相对于事件的基线时间
                        baseline_start = params.baseline_start  # 相对事件的时间，例如 -0.2 表示事件前200ms
                        baseline_end = params.baseline_end      # 相对事件的时间，例如 0 表示事件发生时
                        
                        # 转换为相对分段起始的索引
                        baseline_start_idx = int((baseline_start + params.pre_event) * input_data.sampling_rate)
                        baseline_end_idx = int((baseline_end + params.pre_event) * input_data.sampling_rate)
                        
                        if baseline_start_idx >= 0 and baseline_end_idx <= len(segment_times):
                            # 对每个通道应用基线校正
                            for channel in input_data.channels:
                                baseline = np.mean(segment_data[channel][baseline_start_idx:baseline_end_idx])
                                segment_data[channel] = [val - baseline for val in segment_data[channel]]
                    
                    # 创建单个分段的数据
                    segmented_datasets.append({
                        "data": segment_data,
                        "times": segment_times,
                        "event": event.name,
                        "event_time": event_time,
                        "start": segment_start,
                        "end": segment_end
                    })
                
                # 合并所有分段 (此处简化处理，实际可能需要更复杂的逻辑)
                # 对于事件相关的分段，我们可以选择只返回第一个分段，或者平均所有分段
                # 这里我们简化为只返回第一个分段
                if segmented_datasets:
                    first_segment = segmented_datasets[0]
                    
                    result = RawEEGData(
                        data=first_segment["data"],
                        times=first_segment["times"],
                        channels=input_data.channels,
                        duration=first_segment["end"] - first_segment["start"],
                        sampling_rate=input_data.sampling_rate,
                        dataset_id=dataset_id,
                        subject_id=subject_id,
                        segment_info={
                            "mode": "event",
                            "event": params.event_name,
                            "pre_event": params.pre_event,
                            "post_event": params.post_event,
                            "baseline": {
                                "applied": params.apply_baseline,
                                "start": params.baseline_start,
                                "end": params.baseline_end
                            },
                            "segments_count": len(segmented_datasets)
                        }
                    )
                else:
                    raise ValueError("未能创建任何有效的分段")
            else:
                raise ValueError(f"不支持的分段模式: {params.segment_mode}")
            
            # 计算处理时间
            process_time = time.time() - start_time
            print(f"分段处理完成，耗时: {process_time:.2f}秒")
            
            # 缓存处理结果
            params_dict = params.dict()
            metadata = {
                'params': params_dict,
                'process_time': process_time,
                'timestamp': time.time()
            }
            
            save_metadata(cache_meta_key, metadata)
            save_to_cache(cache_key, result)
            print(f"已缓存分段结果: {cache_key}")
            
            return result
        except Exception as e:
            error_msg = f"分段处理失败: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)

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