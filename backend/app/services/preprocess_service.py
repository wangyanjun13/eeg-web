from pathlib import Path
import numpy as np
from app.models.data_preprocess import FilterParams, ICAParams, ArtifactParams, PreprocessedData, PreprocessParams, SegmentParams, BadSegmentParams, ResampleParams, BadChannelParams, ReferenceParams
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
        """运行ICA分析
        
        Args:
            dataset_id: 数据集ID
            subject_id: 受试者ID
            params: ICA参数，包括方法、组件数量、自动伪迹检测等
            
        Returns:
            RawEEGData: 处理后的数据
        """
        try:
            # 检查ICA参数
            if not params.run_ica:
                print("ICA分析已禁用，返回原始数据")
                return self.get_input_data_for_step(dataset_id, subject_id, "ica")
            
            # 检查组件数量
            if params.n_components is not None and params.n_components <= 0:
                raise ValueError("ICA组件数量必须大于0")
            
            # 检查ICA方法
            valid_methods = ["fastica", "infomax", "extended-infomax"]
            if params.ica_method not in valid_methods:
                raise ValueError(f"不支持的ICA方法: {params.ica_method}，可用方法: {', '.join(valid_methods)}")
                
            # 检查缓存
            cache_key = get_preprocess_cache_key(dataset_id, subject_id, "ica")
            cache_meta_key = f"{cache_key}:meta"
            
            # 从参数中提取通道信息
            channels = params.dict().pop("channels", None) if hasattr(params, "channels") else None
            
            # 创建缓存参数字典，包含通道信息
            params_dict = params.dict()
            if channels:
                params_dict['channels'] = channels
                
            # 检查缓存
            cached_meta = get_metadata(cache_meta_key)
            if cached_meta and cached_meta.get('params') == params_dict:
                cached_data = get_from_cache(cache_key)
                if cached_data:
                    print(f"使用缓存的ICA结果: {cache_key}")
                    return cached_data
                    
            # 没有缓存，执行处理
            start_time = time.time()
            
            # 获取原始数据（应该是前一步骤的结果，例如重参考）
            input_data = self.get_input_data_for_step(dataset_id, subject_id, "ica")
            
            if isinstance(input_data, RawEEGData) and hasattr(input_data, 'error') and input_data.error:
                raise ValueError(input_data.error)
            
            # 确保数据有效
            if not input_data or not input_data.data or not input_data.channels:
                raise ValueError(f"无法获取有效的EEG数据: dataset_id={dataset_id}, subject_id={subject_id}")
            
            print(f"开始执行ICA分析，方法: {params.ica_method}, 组件数量: {params.n_components}")
            
            # 确定要处理的通道
            process_channels = channels if channels else input_data.channels
            print(f"处理通道数量: {len(process_channels)}")
            
            # 转换为MNE格式进行高级处理
            try:
                # 构建EEG原始数据阵列
                channel_data = []
                selected_channels = []
                
                for channel in process_channels:
                    if channel in input_data.data:
                        channel_data.append(input_data.data[channel])
                        selected_channels.append(channel)
                
                if not channel_data:
                    raise ValueError("所选通道无数据")
                
                # 转换为numpy数组
                data_array = np.array(channel_data)
                
                # 创建MNE Raw对象进行ICA处理
                from mne.io import RawArray
                from mne import create_info
                
                # 创建info对象
                info = create_info(
                    ch_names=selected_channels,
                    sfreq=input_data.sampling_rate,
                    ch_types=['eeg'] * len(selected_channels)
                )
                
                # 创建Raw对象
                raw = RawArray(data_array, info)
                
                # 检查是否需要高通滤波来提高ICA效果
                if raw.info['highpass'] < 0.5:  # 如果高通滤波低于0.5Hz
                    print("正在进行高通滤波以提高ICA效果（临时处理不影响原始数据）")
                    raw_for_ica = raw.copy().filter(l_freq=1.0, h_freq=None)
                else:
                    raw_for_ica = raw
                
                # 确定最终组件数量
                if params.n_components is None:
                    # 如果未指定，使用通道数量的70%作为默认值
                    n_components = min(len(selected_channels) - 1, max(5, int(len(selected_channels) * 0.7)))
                else:
                    # 确保不超过通道数量-1
                    n_components = min(params.n_components, len(selected_channels) - 1)
                
                print(f"使用组件数量: {n_components}")
                
                # 运行ICA
                from mne.preprocessing import ICA
                
                # 不同ICA方法的处理
                method_map = {
                    "fastica": "fastica",
                    "infomax": "infomax",
                    "extended-infomax": "extended-infomax"
                }
                
                # 创建ICA对象
                ica = ICA(
                    n_components=n_components,
                    method=method_map[params.ica_method],
                    random_state=42  # 固定随机种子以保证结果可重复
                )
                
                # 拟合ICA
                ica.fit(raw_for_ica)
                
                # 自动检测眼动伪迹
                excluded_components = []
                if params.auto_detect_artifacts:
                    try:
                        # 尝试使用EOG通道自动检测眼动伪迹
                        eog_indices, eog_scores = ica.find_bads_eog(raw_for_ica)
                        if eog_indices:
                            print(f"自动检测到眼动伪迹组件: {eog_indices}")
                            excluded_components.extend(eog_indices)
                    except Exception as e:
                        print(f"自动检测眼动伪迹失败，将使用基于相关性的启发式方法: {str(e)}")
                        
                        # 如果无法使用EOG通道，使用启发式方法 - 检查前额通道的相关性
                        frontal_channels = [ch for ch in selected_channels if 
                                          ch.startswith(('Fp', 'F', 'AF')) or 
                                          ch in ['FP1', 'FP2', 'FPZ']]
                        
                        if frontal_channels:
                            print(f"使用前额通道检测眼动伪迹: {frontal_channels}")
                            
                            # 为每个组件计算与前额通道的相关性
                            for comp_idx in range(n_components):
                                comp_data = ica.get_sources(raw_for_ica).get_data()[comp_idx]
                                
                                # 计算与前额通道的最大相关性
                                max_corr = 0
                                for ch in frontal_channels:
                                    ch_idx = selected_channels.index(ch)
                                    ch_data = data_array[ch_idx]
                                    corr = np.abs(np.corrcoef(comp_data, ch_data)[0, 1])
                                    max_corr = max(max_corr, corr)
                                
                                # 如果相关性很高，认为是眼动伪迹
                                if max_corr > 0.8:  # 通常眼动伪迹与前额通道相关性很高
                                    excluded_components.append(comp_idx)
                                    print(f"检测到可能的眼动伪迹组件: {comp_idx}, 相关性: {max_corr:.3f}")
                
                # 如果检测到伪迹组件，将其排除
                if excluded_components:
                    ica.exclude = excluded_components
                    print(f"排除伪迹组件: {excluded_components}")
                
                # 应用ICA - 使用原始raw对象而非高通滤波后的raw_for_ica
                ica_raw = ica.apply(raw)
                # 获取处理后的数据
                cleaned_data = ica_raw.get_data()
                
                # 保存处理结果
                processed_data = {}
                
                # 对于处理过的通道，使用ICA处理后的数据
                for i, ch in enumerate(selected_channels):
                    processed_data[ch] = cleaned_data[i].tolist()
                
                # 对于未处理的通道，保留原始数据
                for ch in input_data.channels:
                    if ch not in processed_data and ch in input_data.data:
                        processed_data[ch] = input_data.data[ch]
                
                # 创建结果对象
                result = RawEEGData(
                    data=processed_data,
                    times=input_data.times,
                    channels=input_data.channels,
                    duration=input_data.duration,
                    sampling_rate=input_data.sampling_rate,
                    dataset_id=dataset_id,
                    subject_id=subject_id,
                    # 保存原始时间范围
                    timeRange=input_data.timeRange if hasattr(input_data, 'timeRange') else None
                )
                
                # 添加ICA处理信息
                ica_info = {
                    "method": params.ica_method,
                    "n_components": n_components,
                    "excluded_components": excluded_components
                }
                
                # 如果result没有segment_info属性，添加一个
                if not hasattr(result, 'segment_info') or result.segment_info is None:
                    result.segment_info = {}
                    
                # 添加ICA信息
                if isinstance(result.segment_info, dict):
                    result.segment_info["ica_info"] = ica_info
                
                # 计算处理时间并缓存结果
                process_time = time.time() - start_time
                print(f"ICA处理完成，耗时: {process_time:.2f}秒")
                
                metadata = {
                    'params': params_dict,
                    'process_time': process_time,
                    'timestamp': time.time()
                }
                
                save_metadata(cache_meta_key, metadata)
                save_to_cache(cache_key, result)
                
                return result
                
            except Exception as e:
                print(f"ICA处理过程中出错: {str(e)}")
                import traceback
                print(traceback.format_exc())
                raise ValueError(f"ICA处理失败: {str(e)}")
                
        except Exception as e:
            error_msg = f"ICA分析失败: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)

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
    
    def _detect_bad_channels(self, data, method="correlation", threshold=None):
        """检测坏通道
        
        Args:
            data: EEG数据
            method: 检测方法 ('correlation', 'variance', 'spectrum')
            threshold: 阈值 (如果为None则使用自动阈值)
            
        Returns:
            检测到的坏通道列表
        """
        if not data or not data.data or not data.channels:
            print("无效的EEG数据输入")
            return []
        
        print(f"开始坏通道检测: 方法={method}, 自定义阈值={threshold}")
        
        # 确保数据预处理
        channels = data.channels
        # 将数据转换为numpy数组，便于计算
        eeg_data = np.zeros((len(channels), len(data.times)))
        for i, ch in enumerate(channels):
            if ch in data.data:
                # 截取匹配长度
                ch_data = data.data[ch][:len(data.times)] if len(data.data[ch]) > len(data.times) else data.data[ch]
                # 填充数据
                eeg_data[i, :len(ch_data)] = ch_data
            
        bad_channels = []
        
        # 根据不同方法检测坏通道
        if method == "correlation":
            # 使用更敏感的默认阈值 
            corr_threshold = threshold if threshold is not None else 0.2  # 从0.3降低到0.2
            
            # 计算通道间相关性矩阵
            correlation_matrix = np.corrcoef(eeg_data)
            np.fill_diagonal(correlation_matrix, 0)  # 忽略自相关
            
            # 计算每个通道与其他通道的平均相关性
            mean_correlations = np.nanmean(correlation_matrix, axis=1)
            
            # 打印每个通道的相关性值，便于调试
            for i, ch in enumerate(channels):
                print(f"通道 {ch} 的平均相关性: {mean_correlations[i]:.4f}")
            
            # 寻找平均相关性低于阈值的通道
            for i, corr in enumerate(mean_correlations):
                if corr < corr_threshold:
                    bad_channels.append(channels[i])
                    print(f"检测到坏通道(相关性方法): {channels[i]}, 相关性值: {corr:.4f}")
            
        elif method == "variance":
            # 方差方法：检测方差异常高或异常低的通道
            # 降低阈值倍数，使检测更敏感
            z_threshold = threshold if threshold is not None else 2.0  # 从2.5降低到2.0
            
            # 计算每个通道的方差
            variances = np.var(eeg_data, axis=1)
            
            # 计算方差的均值和标准差
            mean_var = np.mean(variances)
            std_var = np.std(variances)
            
            # 打印每个通道的方差值，便于调试
            for i, ch in enumerate(channels):
                z_score = abs(variances[i] - mean_var) / (std_var + 1e-10)
                print(f"通道 {ch} 的方差: {variances[i]:.4f}, Z分数: {z_score:.4f}")
            
            # 检测方差异常的通道
            for i, var in enumerate(variances):
                z_score = abs(var - mean_var) / (std_var + 1e-10)  # 避免除零
                if z_score > z_threshold:
                    bad_channels.append(channels[i])
                    print(f"检测到坏通道(方差方法): {channels[i]}, Z分数: {z_score:.4f}")
            
        elif method == "spectrum":
            # 功率谱方法：检测频谱特性异常的通道
            from scipy import signal
            
            # 采样率
            fs = data.sampling_rate
            
            # 计算每个通道的功率谱
            psds = []
            for i in range(len(channels)):
                # 使用Welch方法计算功率谱密度
                f, psd = signal.welch(eeg_data[i], fs, nperseg=min(256, len(eeg_data[i])))
                psds.append(psd)
            
            psds = np.array(psds)
            
            # 计算平均功率谱
            mean_psd = np.mean(psds, axis=0)
            
            # 为每个通道计算与平均功率谱的差异
            psd_diffs = []
            for i in range(len(channels)):
                # 计算对数功率谱差异
                diff = np.mean(np.abs(np.log10(psds[i] + 1e-10) - np.log10(mean_psd + 1e-10)))
                psd_diffs.append(diff)
            
            # 设置自动阈值 - 降低阈值使检测更敏感
            spec_threshold = threshold if threshold is not None else 0.4  # 从0.5降低到0.4
            
            # 打印每个通道的频谱差异，便于调试
            for i, ch in enumerate(channels):
                print(f"通道 {ch} 的频谱差异: {psd_diffs[i]:.4f}")
            
            # 检测频谱异常的通道
            for i, diff in enumerate(psd_diffs):
                if diff > spec_threshold:
                    bad_channels.append(channels[i])
                    print(f"检测到坏通道(频谱方法): {channels[i]}, 差异值: {diff:.4f}")
        
        # 输出检测结果
        if bad_channels:
            print(f"检测到 {len(bad_channels)} 个坏通道: {bad_channels}")
        else:
            print(f"使用 {method} 方法未检测到坏通道，考虑调低阈值重试")
        
        return bad_channels

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
        """对数据进行分段"""
        try:
            # 获取输入数据
            input_data = self.dataset_service.get_subject_data(
                dataset_id, 
                subject_id,
                start_time=params.start_time if not params.use_original_full_data else 0,
                duration=None if params.use_original_full_data else (params.end_time - params.start_time)
            )
            
            if not input_data or not input_data.data:
                raise ValueError("无法获取有效的输入数据")
            
            # 确保数据中不包含非标准浮点值
            sanitized_data = {}
            for channel in input_data.channels:
                if channel in input_data.data:
                    channel_data = input_data.data[channel]
                    sanitized_data[channel] = [0.0 if (np.isnan(x) or np.isinf(x)) else float(x) for x in channel_data]
            
            # 基于分段模式选择不同处理
            if params.segment_mode == "time":
                # 时间窗口分段 - 现有逻辑
                # ... [现有时间窗口分段代码保持不变] ...
                
                # 计算时间范围和对应索引
                time_array = input_data.times
                sampling_rate = input_data.sampling_rate
                
                # 找到开始和结束时间对应的索引
                start_idx = 0
                end_idx = len(time_array) - 1
                
                for i, t in enumerate(time_array):
                    if t >= params.start_time:
                        start_idx = i
                        break
                
                for i in range(start_idx, len(time_array)):
                    if time_array[i] >= params.end_time:
                        end_idx = i
                        break
                
                # 提取所选时间窗口的数据
                segmented_data = {}
                for channel in input_data.channels:
                    if channel in sanitized_data:
                        segmented_data[channel] = sanitized_data[channel][start_idx:end_idx]
                
                # 创建新的时间数组，均匀分布在整个时间窗口中
                segmented_times = []
                total_points = end_idx - start_idx
                segment_duration = params.end_time - params.start_time
                
                # 确保均匀覆盖整个选定时间窗口
                for i in range(total_points):
                    if total_points > 1:
                        relative_position = i / (total_points - 1)
                    else:
                        relative_position = 0
                    segmented_times.append(params.start_time + relative_position * segment_duration)
                
                # 创建结果
                result = RawEEGData(
                    data=segmented_data,
                    times=segmented_times,
                    channels=input_data.channels,
                    duration=params.end_time - params.start_time,
                    sampling_rate=input_data.sampling_rate,
                    dataset_id=dataset_id,
                    subject_id=subject_id,
                    segment_info={
                        "type": "time_window",
                        "start": params.start_time,
                        "end": params.end_time,
                        "use_original_full_data": params.use_original_full_data
                    }
                )
                
            elif params.segment_mode == "event":
                # 新增：基于事件的分段
                if not params.event_id:
                    raise ValueError("事件分段模式下必须指定event_id")
                    
                # 获取事件信息
                events_info = self.dataset_service.get_events_info(dataset_id, subject_id)
                events = events_info.get("events", [])
                
                # 如果不使用完整原始数据，则过滤当前时间窗口内的事件
                if not params.use_original_full_data and params.start_time is not None and params.end_time is not None:
                    time_window_events = []
                    for event in events:
                        event_onset = float(event.get("onset", 0))
                        if params.start_time <= event_onset <= params.end_time:
                            time_window_events.append(event)
                    events = time_window_events
                
                # 查找目标事件
                target_events = []
                for event in events:
                    if str(event.get("id")) == str(params.event_id):
                        target_events.append(event)
                
                if not target_events:
                    if not params.use_original_full_data and params.start_time is not None and params.end_time is not None:
                        error_msg = f"在时间窗口 {params.start_time}-{params.end_time}s 内未找到指定的事件类型: {params.event_id}"
                    else:
                        error_msg = f"未找到指定的事件类型: {params.event_id}"
                    raise ValueError(error_msg)
                    
                # 计算每个事件的时间窗口并合并
                time_array = input_data.times
                sampling_rate = input_data.sampling_rate
                duration = params.time_before + params.time_after
                
                # 创建空的合并数据结构
                segmented_data = {channel: [] for channel in input_data.channels if channel in sanitized_data}
                segmented_times = []
                
                # 对每个事件进行处理
                for event in target_events:
                    event_onset = float(event.get("onset", 0))
                    seg_start = event_onset - params.time_before
                    seg_end = event_onset + params.time_after
                    
                    # 找到对应的索引
                    start_idx = 0
                    end_idx = len(time_array) - 1
                    
                    for i, t in enumerate(time_array):
                        if t >= seg_start:
                            start_idx = i
                            break
                    
                    for i in range(start_idx, len(time_array)):
                        if time_array[i] >= seg_end:
                            end_idx = i
                            break
                    
                    # 提取数据
                    event_times = [t - seg_start for t in time_array[start_idx:end_idx]]
                    
                    # 如果是第一个事件，设置时间数组
                    if not segmented_times:
                        segmented_times = event_times
                    
                    # 只有时间数组长度匹配时才合并数据（确保所有事件片段长度一致）
                    if len(event_times) == len(segmented_times):
                        for channel in input_data.channels:
                            if channel in sanitized_data:
                                channel_data = sanitized_data[channel][start_idx:end_idx]
                                # 如果是第一个事件，直接设置数据
                                if not segmented_data[channel]:
                                    segmented_data[channel] = channel_data
                                else:
                                    # 累加数据进行平均
                                    for i in range(len(channel_data)):
                                        segmented_data[channel][i] += channel_data[i]
                
                # 计算平均值
                if target_events:
                    for channel in segmented_data:
                        segmented_data[channel] = [x / len(target_events) for x in segmented_data[channel]]
                
                # 创建结果
                result = RawEEGData(
                    data=segmented_data,
                    times=segmented_times,
                    channels=input_data.channels,
                    duration=duration,
                    sampling_rate=input_data.sampling_rate,
                    dataset_id=dataset_id,
                    subject_id=subject_id,
                    segment_info={
                        "type": "event_related",
                        "event_id": params.event_id,
                        "time_before": params.time_before,
                        "time_after": params.time_after,
                        "event_count": len(target_events),
                        "original_events": [float(event.get("onset", 0)) for event in target_events],
                        "original_time_window": [params.start_time, params.end_time] if not params.use_original_full_data else None
                    }
                )
            else:
                raise ValueError(f"不支持的分段模式: {params.segment_mode}")
            
            # 应用基线校正（如果需要）
            if params.apply_baseline:
                result = self._apply_baseline_correction(
                    result, params.baseline_start, params.baseline_end
                )
            
            return result
        except Exception as e:
            import traceback
            print(f"分段处理失败: {str(e)}")
            print(traceback.format_exc())
            raise ValueError(f"分段处理失败: {str(e)}")

    def _apply_baseline_correction(self, raw_data: RawEEGData, start: float, end: float) -> RawEEGData:
        """简化的基线校正功能"""
        try:
            # 转换为numpy数组进行处理
            data_dict = raw_data.data
            times = raw_data.times
            
            # 找到基线范围的索引
            start_idx = 0
            for i, t in enumerate(times):
                if t >= start:
                    start_idx = i
                    break
                
            end_idx = len(times) - 1
            for i, t in enumerate(times[start_idx:], start_idx):
                if t >= end:
                    end_idx = i
                    break
            
            # 对每个通道应用基线校正
            for channel in data_dict.keys():
                try:
                    channel_data = np.array(data_dict[channel])
                    if len(channel_data) > end_idx and end_idx >= start_idx:
                        baseline_mean = np.mean(channel_data[start_idx:end_idx+1])
                        channel_data = channel_data - baseline_mean
                        data_dict[channel] = channel_data.tolist()
                except Exception as channel_error:
                    print(f"警告: 通道 {channel} 基线校正失败: {str(channel_error)}")
            
            # 创建新的RawEEGData对象，保留所有原始字段
            result = RawEEGData(
                data=data_dict,
                times=times,
                channels=raw_data.channels,
                duration=raw_data.duration,
                sampling_rate=raw_data.sampling_rate,
                dataset_id=raw_data.dataset_id,
                subject_id=raw_data.subject_id,
                segment_info=raw_data.segment_info
            )
            
            # 更新分段信息，添加基线校正信息
            if result.segment_info:
                result.segment_info["baseline_corrected"] = True
                result.segment_info["baseline_start"] = start
                result.segment_info["baseline_end"] = end
            
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

    def process_bad_channels(self, dataset_id: str, subject_id: str, params: BadChannelParams) -> RawEEGData:
        """处理坏通道 - 检测并应用处理方法
        
        Args:
            dataset_id: 数据集ID
            subject_id: 受试者ID
            params: 坏通道检测与处理参数
            
        Returns:
            处理后的数据对象
        """
        try:
            # 检查缓存
            cache_key = get_preprocess_cache_key(dataset_id, subject_id, "bad_channels")
            cache_meta_key = f"{cache_key}:meta"
            
            # 首先检查元数据，比对参数判断缓存是否有效
            cached_meta = get_metadata(cache_meta_key)
            if cached_meta:
                # 检查参数是否匹配
                params_dict = params.dict()
                
                # 参数一致则返回缓存的结果
                if cached_meta.get('params') == params_dict:
                    print(f"找到有效的坏通道处理缓存: {cache_key}")
                    cached_data = get_from_cache(cache_key)
                    if cached_data:
                        return cached_data

            print(f"执行坏通道检测和处理")
            start_time = time.time()
            
            # 获取输入数据（应该是前一步骤的结果）
            input_data = self.get_input_data_for_step(dataset_id, subject_id, "badChannels")
            
            if isinstance(input_data, RawEEGData) and hasattr(input_data, 'error') and input_data.error:
                raise ValueError(input_data.error)
            
            # 如果不需要检测坏通道，直接返回输入数据
            if not params.detect_bad_channels:
                return input_data
            
            # 检测坏通道
            bad_channels = []
            
            # 如果提供了自定义坏通道列表，直接使用
            if params.use_custom_bads and params.custom_bad_channels:
                bad_channels = params.custom_bad_channels
            else:
                # 根据参数选择的方法检测坏通道
                bad_channels = self._detect_bad_channels(
                    input_data, 
                    method=params.bad_channel_method,
                    threshold=params.threshold
                )
            
            # 记录检测到的坏通道数量和名称 (用于日志)
            print(f"检测到 {len(bad_channels)} 个坏通道: {', '.join(bad_channels) if bad_channels else '无'}")
            
            # 处理检测到的坏通道
            processed_data = {}
            result_channels = input_data.channels.copy()
            
            # 使用不同的处理模式
            if params.rejection_mode == "zero":
                # 将坏通道数据清零
                for channel in input_data.channels:
                    if channel in bad_channels:
                        # 创建与原始数据等长的零数组
                        channel_length = len(input_data.data[channel])
                        processed_data[channel] = [0.0] * channel_length
                    else:
                        # 保留良好通道的原始数据
                        processed_data[channel] = input_data.data[channel]
                    
            elif params.rejection_mode == "interpolate":
                # 尝试插值坏通道
                try:
                    # 转换为MNE-Python的Raw对象
                    raw_mne = self._convert_to_mne_raw(input_data)
                    
                    # 设置坏通道
                    raw_mne.info['bads'] = bad_channels
                    
                    # 使用球面样条插值
                    raw_mne.interpolate_bads(reset_bads=True)
                    
                    # 从Raw对象中提取数据
                    data_array, _ = raw_mne[:, :]
                    
                    # 重新格式化为字典格式
                    for i, ch in enumerate(raw_mne.ch_names):
                        processed_data[ch] = data_array[i, :].tolist()
                    
                    # 更新通道列表，确保与MNE处理后一致
                    result_channels = raw_mne.ch_names
                    
                except Exception as interp_error:
                    print(f"插值失败: {str(interp_error)}，回退到零填充")
                    # 如果插值失败，回退到零填充
                    for channel in input_data.channels:
                        if channel in bad_channels:
                            channel_length = len(input_data.data[channel])
                            processed_data[channel] = [0.0] * channel_length
                        else:
                            processed_data[channel] = input_data.data[channel]
                
            elif params.rejection_mode == "remove":
                # 从数据集中移除坏通道
                for channel in input_data.channels:
                    if channel not in bad_channels:
                        processed_data[channel] = input_data.data[channel]
                    
                # 更新通道列表，移除坏通道
                result_channels = [ch for ch in input_data.channels if ch not in bad_channels]
            
            else:
                # 未知的处理模式，保持原始数据不变
                processed_data = input_data.data
            
            # 创建结果对象
            result = RawEEGData(
                data=processed_data,
                times=input_data.times,
                channels=result_channels,
                duration=input_data.duration,
                sampling_rate=input_data.sampling_rate,
                dataset_id=dataset_id,
                subject_id=subject_id,
                bad_channels=bad_channels
            )
            
            # 计算处理时间
            process_time = time.time() - start_time
            print(f"坏通道处理完成，耗时: {process_time:.2f}秒")
            
            # 缓存处理结果
            params_dict = params.dict()
            metadata = {
                'params': params_dict,
                'process_time': process_time,
                'timestamp': time.time()
            }
            
            save_metadata(cache_meta_key, metadata)
            save_to_cache(cache_key, result)
            print(f"已缓存坏通道处理结果: {cache_key}")
            
            return result
        
        except Exception as e:
            error_msg = f"坏通道处理失败: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)

    def _convert_to_mne_raw(self, raw_eeg_data):
        """将RawEEGData转换为MNE Raw对象，便于进行高级处理
        
        Args:
            raw_eeg_data: 自定义EEG数据对象
            
        Returns:
            mne.io.Raw: MNE Raw对象
        """
        import mne
        import numpy as np
        
        # 从数据中提取通道和采样率
        channels = raw_eeg_data.channels
        sampling_rate = raw_eeg_data.sampling_rate
        
        # 将数据转换为numpy数组
        data = np.zeros((len(channels), len(raw_eeg_data.times)))
        for i, ch in enumerate(channels):
            if ch in raw_eeg_data.data:
                # 确保数据长度匹配
                channel_data = raw_eeg_data.data[ch]
                data_length = min(len(channel_data), len(raw_eeg_data.times))
                data[i, :data_length] = channel_data[:data_length]
        
        # 创建Info对象
        info = mne.create_info(
            ch_names=channels,
            sfreq=sampling_rate,
            ch_types=['eeg'] * len(channels)
        )
        
        # 创建Raw对象
        raw = mne.io.RawArray(data, info)
        
        return raw

    def apply_reference(self, dataset_id: str, subject_id: str, params: ReferenceParams, channels: List[str] = None) -> RawEEGData:
        """应用重参考处理
        
        Args:
            dataset_id: 数据集ID
            subject_id: 受试者ID
            params: 重参考参数
            channels: 处理通道列表（可选）
            
        Returns:
            RawEEGData: 重参考后的数据
        """
        try:
            # 检查缓存
            cache_key = get_preprocess_cache_key(dataset_id, subject_id, "reference")
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
                    print(f"找到有效的重参考缓存: {cache_key}")
                    cached_data = get_from_cache(cache_key)
                    if cached_data:
                        # 确保时间范围信息存在
                        if params.time_range and hasattr(cached_data, 'timeRange'):
                            cached_data.timeRange = params.time_range
                        return cached_data

            # 缓存无效或不存在，执行重参考处理
            print(f"执行重参考处理: 方式={params.reference}")
            start_time = time.time()
            
            # 获取输入数据（应该是前一步骤的结果）
            input_data = self.get_input_data_for_step(dataset_id, subject_id, "reference")
            
            if isinstance(input_data, RawEEGData) and hasattr(input_data, 'error') and input_data.error:
                raise ValueError(input_data.error)
            
            # 诊断原始数据
            print(f"处理前数据信息 - 通道数: {len(input_data.channels)}, 时间点数: {len(input_data.times)}")
            
            # 查看几个通道的数据范围
            for ch in input_data.channels[:3]:
                if ch in input_data.data:
                    ch_data = input_data.data[ch]
                    print(f"通道 {ch} 数据 - 最小值: {min(ch_data):.2f}, 最大值: {max(ch_data):.2f}, 平均值: {sum(ch_data)/len(ch_data):.2f}")
            
            # 检查时间数据
            if input_data.times and len(input_data.times) > 0:
                print(f"时间数据 - 开始: {input_data.times[0]:.3f}s, 结束: {input_data.times[-1]:.3f}s, 数量: {len(input_data.times)}")
            else:
                print("警告: 输入数据没有时间信息")
            
            # 设置要处理的通道
            process_channels = channels if channels else input_data.channels
            
            # 转换为numpy数组以便处理
            data_array = {}
            for channel in input_data.channels:
                if channel in input_data.data:
                    data_array[channel] = np.array(input_data.data[channel])
            
            # 应用不同的重参考方法
            if params.reference == "average":
                # 平均参考 - 从每个通道减去所有通道的平均值
                print(f"执行平均参考，处理通道数: {len(process_channels)}")
                
                # 1. 使用所有处理通道计算整体平均值
                ref_channels = [ch for ch in process_channels if ch in data_array]
                if not ref_channels:
                    raise ValueError("没有有效的通道用于平均参考")
                
                print(f"参考计算使用的通道: {len(ref_channels)} 个")
                
                # 收集用于平均计算的数据
                data_for_avg = []
                for ch in ref_channels:
                    data_for_avg.append(data_array[ch])
                
                # 使用numpy进行计算，确保平均计算正确
                data_matrix = np.vstack(data_for_avg)  # 堆叠成矩阵
                avg_data = np.mean(data_matrix, axis=0)  # 按列求平均
                
                # 输出平均参考值的统计信息
                print(f"平均参考值 - 最小值: {np.min(avg_data):.2f}, 最大值: {np.max(avg_data):.2f}, 平均值: {np.mean(avg_data):.2f}")
                print(f"平均参考值部分样本: {avg_data[:5]}")
                
                # 移除平均参考 - 确保不对所有信号全部归零
                for ch in input_data.channels:
                    if ch in data_array:
                        # 保存原始信号的描述性统计信息
                        orig_min = np.min(data_array[ch])
                        orig_max = np.max(data_array[ch])
                        orig_mean = np.mean(data_array[ch])
                        
                        # 减去平均参考
                        data_array[ch] = data_array[ch] - avg_data
                        
                        # 信号处理后的统计信息
                        new_min = np.min(data_array[ch])
                        new_max = np.max(data_array[ch])
                        new_mean = np.mean(data_array[ch])
                        
                        # 只打印前几个通道的统计信息避免日志过多
                        if ch in input_data.channels[:3]:
                            print(f"通道 {ch} 重参考后 - 最小值: {new_min:.2f}(原{orig_min:.2f}), "
                                 f"最大值: {new_max:.2f}(原{orig_max:.2f}), "
                                 f"平均值: {new_mean:.2f}(原{orig_mean:.2f})")
            
            # 保持mastoids和custom参考不变
            elif params.reference == "mastoids":
                # 双侧乳突参考 (M1+M2)/2
                mastoid_channels = ["M1", "M2"]  # 常见的乳突通道
                alt_mastoid_channels = ["TP9", "TP10"]  # 替代的乳突位置
                
                # 检查是否存在乳突通道
                available_mastoids = [ch for ch in mastoid_channels if ch in data_array]
                
                # 如果没有标准乳突通道，尝试使用替代通道
                if not available_mastoids:
                    available_mastoids = [ch for ch in alt_mastoid_channels if ch in data_array]
                
                if not available_mastoids:
                    raise ValueError("未找到乳突通道(M1/M2或TP9/TP10)，无法应用乳突参考")
                
                print(f"使用乳突通道: {available_mastoids}")
                
                # 计算乳突通道的平均值 - 使用正确的矩阵方法
                mastoid_data_arr = np.vstack([data_array[ch] for ch in available_mastoids])
                mastoid_data = np.mean(mastoid_data_arr, axis=0)
                
                # 输出乳突参考值的统计信息
                print(f"乳突参考值 - 最小值: {np.min(mastoid_data):.2f}, 最大值: {np.max(mastoid_data):.2f}")
                print(f"乳突参考值部分样本: {mastoid_data[:5]}")
                
                # 从每个通道减去乳突平均值
                proc_count = 0
                for ch in input_data.channels:
                    if ch in data_array and ch not in available_mastoids:  # 不对乳突通道自身重参考
                        data_array[ch] = data_array[ch] - mastoid_data
                        proc_count += 1
                
                print(f"乳突参考完成，处理了 {proc_count} 个通道")
                
            elif params.reference == "custom":
                # 自定义参考 - 使用指定通道作为参考
                if not params.custom_ref_channels:
                    raise ValueError("自定义参考模式下必须指定参考通道")
                
                # 确保自定义参考通道存在
                ref_channels = [ch for ch in params.custom_ref_channels if ch in data_array]
                
                if not ref_channels:
                    raise ValueError(f"指定的参考通道不存在或无效: {params.custom_ref_channels}")
                
                print(f"使用自定义参考通道: {ref_channels}")
                
                # 计算参考通道的平均值 - 使用正确的矩阵方法
                ref_data_arr = np.vstack([data_array[ch] for ch in ref_channels])
                ref_data = np.mean(ref_data_arr, axis=0)
                
                # 输出自定义参考值的统计信息
                print(f"自定义参考值 - 最小值: {np.min(ref_data):.2f}, 最大值: {np.max(ref_data):.2f}")
                print(f"自定义参考值部分样本: {ref_data[:5]}")
                
                # 从每个通道减去参考值
                proc_count = 0
                for ch in input_data.channels:
                    if ch in data_array and ch not in ref_channels:  # 不对参考通道自身重参考
                        data_array[ch] = data_array[ch] - ref_data
                        proc_count += 1
                
                print(f"自定义参考完成，处理了 {proc_count} 个通道")
            else:
                raise ValueError(f"不支持的重参考方式: {params.reference}")
            
            # 转换回列表格式
            referenced_data = {}
            for ch in input_data.channels:
                if ch in data_array:
                    referenced_data[ch] = data_array[ch].tolist()
                else:
                    referenced_data[ch] = input_data.data[ch]
            
            # 确保时间数据正确
            if not input_data.times or len(input_data.times) == 0:
                print("警告: 创建默认时间序列，因为输入数据没有时间信息")
                # 创建与数据长度匹配的默认时间轴
                first_channel = next(iter(referenced_data.values())) if referenced_data else []
                data_length = len(first_channel)
                if data_length > 0:
                    times = [i * input_data.duration / (data_length - 1) for i in range(data_length)]
                else:
                    times = []
            else:
                # 检查时间数据的有效性
                times = input_data.times
                # 验证时间数据是否单调递增且覆盖合理范围
                if len(times) > 1:
                    time_range = times[-1] - times[0]
                    if time_range < 0.001:  # 时间范围过小
                        print("警告: 时间范围过小，创建新的时间序列")
                        first_channel = next(iter(referenced_data.values())) if referenced_data else []
                        data_length = len(first_channel)
                        if data_length > 0:
                            times = [i * input_data.duration / (data_length - 1) for i in range(data_length)]
                        else:
                            times = []
                    elif len(times) > 5 and all(abs(times[i] - times[0]) < 0.0001 for i in range(1, 5)):
                        # 前几个时间点几乎相同，可能有问题
                        print("警告: 时间数据异常，前几个点都相同，创建新的时间序列")
                        first_channel = next(iter(referenced_data.values())) if referenced_data else []
                        data_length = len(first_channel)
                        if data_length > 0:
                            times = [i * input_data.duration / (data_length - 1) for i in range(data_length)]
                        else:
                            times = []
                
            # 打印输出数据结构信息
            print(f"输出数据 - 通道数: {len(input_data.channels)}, 时间点数: {len(times)}")
            if len(times) > 1:
                print(f"时间范围: {times[0]:.3f}s 到 {times[-1]:.3f}s")
            
            for ch in list(referenced_data.keys())[:2]:  # 仅打印前两个通道避免日志过多
                channel_data = referenced_data[ch]
                print(f"输出通道 {ch} - 数据长度: {len(channel_data)}, 样本: [{channel_data[0]:.2f}, {channel_data[1]:.2f}, ...]")
            
            # 创建结果对象
            result = RawEEGData(
                data=referenced_data,
                times=times,
                channels=input_data.channels,
                duration=input_data.duration,
                sampling_rate=input_data.sampling_rate,
                dataset_id=dataset_id,
                subject_id=subject_id
            )
            
            # 处理时间范围 - 优先使用传入的时间范围参数
            if params.time_range and len(params.time_range) == 2:
                print(f"使用传入的时间范围参数: {params.time_range}")
                result.timeRange = params.time_range
            else:
                # 如果没有传入时间范围，尝试使用输入数据的时间范围
                if hasattr(input_data, 'timeRange') and input_data.timeRange:
                    print(f"使用输入数据的时间范围: {input_data.timeRange}")
                    result.timeRange = input_data.timeRange
                else:
                    # 从时间数据计算时间范围
                    if len(times) > 1:
                        result.timeRange = [times[0], times[-1]]
                        print(f"从时间数据计算时间范围: {result.timeRange}")
                    else:
                        print("无法计算有效的时间范围，使用默认值")
                        result.timeRange = [0, input_data.duration]
            
            # 计算处理时间
            process_time = time.time() - start_time
            print(f"重参考处理完成，耗时: {process_time:.2f}秒")
            
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
            print(f"已缓存重参考结果: {cache_key}")
            
            return result
        except Exception as e:
            error_msg = f"重参考处理失败: {str(e)}"
            print(error_msg)
            import traceback
            print(traceback.format_exc())  # 打印完整堆栈跟踪，帮助调试
            raise ValueError(error_msg)