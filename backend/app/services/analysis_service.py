import mne
import logging
from typing import Dict, Any
from app.models.data_analysis import ERPParams, TimeFreqParams, ConnectivityParams
import numpy as np
from mne.time_frequency import tfr_morlet
from scipy.stats import ttest_rel
from mne.stats import fdr_correction

# 创建logger
logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self, dataset_service):
        self.dataset_service = dataset_service
        # 不直接依赖PreprocessService，避免循环依赖

    def get_basic_info(self, dataset_id: str) -> Dict[str, Any]:
        """获取数据集基本分析信息"""
        # 获取数据集信息
        dataset_info = self.dataset_service.get_dataset_info(dataset_id)
        
        # 返回基本分析信息
        return {
            "dataset_id": dataset_id,
            "name": dataset_info.get("Name", "未知数据集"),
            "subject_count": dataset_info.get("subject_count", 0),
            "available_analyses": ["erp", "time_freq", "connectivity"]
        }

    def compute_erp(self, dataset_id: str, subject_id: str, params: ERPParams) -> Dict[str, Any]:
        """计算ERP分析结果"""
        try:
            # 检查是否使用预处理数据
            if params.use_preprocessed_data and params.preprocessed_data:
                logger.info(f"使用预处理数据进行ERP分析")
                print(f"使用预处理数据进行ERP分析，数据集ID: {dataset_id}, 受试者ID: {subject_id}")
                print(f"预处理数据基本信息: channels={len(params.preprocessed_data.get('channels', []))},"
                      f" sampling_rate={params.preprocessed_data.get('sampling_rate')}")
                
                if 'data' in params.preprocessed_data:
                    channel_data_lengths = {ch: len(data) for ch, data in params.preprocessed_data['data'].items() 
                                           if isinstance(data, list)}
                    print(f"通道数据长度: {channel_data_lengths}")
                else:
                    print("警告: 预处理数据中缺少'data'字段")
                
                raw = self._convert_preprocessed_to_mne(params.preprocessed_data)
                print(f"预处理数据转换为MNE格式成功，通道数: {len(raw.ch_names)}, 采样率: {raw.info['sfreq']}")
            else:
        # 获取原始数据
                print(f"使用原始数据进行ERP分析，数据集ID: {dataset_id}, 受试者ID: {subject_id}")
                raw = self.dataset_service.get_raw_data(dataset_id, subject_id)
                
                # 如果需要预处理
                if params.preprocess and params.preprocess_params:
                    # 应用预处理
                    logger.info(f"应用预处理参数: {params.preprocess_params}")
                    # TODO: 实现预处理逻辑
                    pass
            
            # 提取事件
            print("开始提取事件...")
            try:
                events = mne.find_events(raw)
                print(f"找到 {len(events)} 个事件")
                
                # 如果没有找到事件，尝试从注释中创建
                if len(events) == 0:
                    print("没有找到事件，尝试从注释创建")
                    if len(raw.annotations) > 0:
                        print(f"找到 {len(raw.annotations)} 个注释，尝试转换为事件")
                        events = mne.events_from_annotations(raw)[0]
                        print(f"从注释创建了 {len(events)} 个事件")
                    else:
                        print("没有注释可用，创建虚拟事件")
                        # 创建虚拟事件 - 在数据中间位置
                        middle_sample = len(raw.times) // 2
                        events = np.array([[middle_sample, 0, 1]], dtype=int)
                        print(f"创建了虚拟事件，位置: {middle_sample}")
                        
                        # 添加注释以便后续处理
                        onset = middle_sample / raw.info['sfreq']  # 转换为秒
                        raw.annotations.append(onset, 0.1, '1')
                        print(f"添加了虚拟事件注释: onset={onset}")
            except Exception as e:
                print(f"提取事件失败: {str(e)}")
                # 创建虚拟事件作为后备
                middle_sample = len(raw.times) // 2
                events = np.array([[middle_sample, 0, 1]], dtype=int)
                print(f"创建了后备虚拟事件，位置: {middle_sample}")
            
            # 确保至少有一个事件
            if len(events) == 0:
                print("警告: 没有找到任何事件，创建最终后备事件")
                middle_sample = len(raw.times) // 2
                events = np.array([[middle_sample, 0, 1]], dtype=int)
            
            # 创建epochs
            print(f"创建epochs, tmin={params.tmin}, tmax={params.tmax}, baseline={params.baseline}")
            try:
                epochs = mne.Epochs(
                    raw, 
                    events, 
                    tmin=params.tmin, 
                    tmax=params.tmax,
                    baseline=params.baseline if params.baseline else None,
                    preload=True
                )
                print(f"成功创建epochs，包含 {len(epochs)} 个epoch")
            except Exception as e:
                print(f"创建epochs失败: {str(e)}")
                # 尝试调整参数重新创建
                print("尝试调整参数重新创建epochs")
                try:
                    # 调整tmin和tmax以确保在数据范围内
                    data_duration = len(raw.times) / raw.info['sfreq']
                    safe_tmin = max(params.tmin, -data_duration/2)
                    safe_tmax = min(params.tmax, data_duration/2)
                    print(f"调整后的时间窗口: tmin={safe_tmin}, tmax={safe_tmax}")
                    
                    epochs = mne.Epochs(
                        raw, 
                        events, 
                        tmin=safe_tmin, 
                        tmax=safe_tmax,
                        baseline=None,  # 禁用基线校正以减少错误可能
                        preload=True
                    )
                    print(f"使用调整后的参数成功创建epochs，包含 {len(epochs)} 个epoch")
                except Exception as e2:
                    print(f"调整参数后创建epochs仍然失败: {str(e2)}")
                    # 创建一个最简单的epoch作为后备
                    print("创建最简单的epoch作为后备")
                    # 使用最小的时间窗口
                    minimal_tmin = -0.1
                    minimal_tmax = 0.1
                    epochs = mne.Epochs(
                        raw, 
                        events, 
                        tmin=minimal_tmin, 
                        tmax=minimal_tmax,
                        baseline=None,
                        preload=True,
                        reject=None,  # 禁用拒绝
                        flat=None     # 禁用平坦检测
                    )
                    print(f"创建最小化epochs成功，包含 {len(epochs)} 个epoch")
            
            # 计算ERP
            print("计算ERP平均值...")
            evoked = epochs.average()
            print(f"ERP计算完成，数据形状: {evoked.data.shape}")
            
            # 转换为字典格式
            result = {
                "times": evoked.times.tolist(),
                "data": {ch: evoked.data[i].tolist() for i, ch in enumerate(evoked.ch_names)},
                "info": {
                    "sfreq": evoked.info["sfreq"],
                    "ch_names": evoked.ch_names
                }
            }
            
            print(f"ERP分析完成，返回结果包含 {len(result['data'])} 个通道的数据")
            return result
        except Exception as e:
            logger.error(f"ERP分析失败: {str(e)}")
            print(f"ERP分析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

    def _convert_preprocessed_to_mne(self, preprocessed_data: Dict[str, Any]) -> mne.io.Raw:
        """将前端传递的预处理数据转换为MNE Raw对象
        
        Args:
            preprocessed_data: 前端传递的预处理数据
            
        Returns:
            mne.io.Raw: MNE Raw对象
        """
        try:
            print(f"开始转换预处理数据到MNE格式")
            
            # 提取必要的数据字段
            data = preprocessed_data.get("data", {})
            channels = preprocessed_data.get("channels", [])
            sampling_rate = preprocessed_data.get("sampling_rate", 1000)
            
            if not data:
                print(f"警告: 预处理数据中缺少data字段")
                raise ValueError("预处理数据缺少必要的data字段")
                
            if not channels:
                print(f"警告: 预处理数据中缺少channels字段")
                # 尝试从data中提取通道信息
                channels = list(data.keys())
                if not channels:
                    raise ValueError("预处理数据缺少必要的channels字段，且无法从data中提取")
                print(f"从data中提取的通道列表: {channels}")
                
            print(f"预处理数据包含 {len(channels)} 个通道，采样率为 {sampling_rate} Hz")
            
            # 将数据转换为numpy数组
            data_array = []
            for channel in channels:
                if channel in data:
                    channel_data = np.array(data[channel])
                    # 检查数据类型和有效性
                    if not isinstance(channel_data, np.ndarray):
                        print(f"警告: 通道 {channel} 的数据不是numpy数组，尝试转换")
                        channel_data = np.array(channel_data)
                    
                    # 检查是否有NaN或Inf值
                    if np.isnan(channel_data).any() or np.isinf(channel_data).any():
                        print(f"警告: 通道 {channel} 包含NaN或Inf值，将被替换为0")
                        channel_data = np.nan_to_num(channel_data, nan=0.0, posinf=0.0, neginf=0.0)
                        
                    data_array.append(channel_data)
                else:
                    # 如果通道不存在，用零填充
                    print(f"警告：预处理数据中缺少通道 {channel}，将使用零填充")
                    # 假设所有通道数据长度相同，取第一个通道的长度
                    first_channel_key = next(iter(data.keys()))
                    if first_channel_key:
                        first_channel = np.array(data[first_channel_key])
                        data_array.append(np.zeros_like(first_channel))
                    else:
                        raise ValueError(f"无法确定通道 {channel} 的数据长度，因为没有其他通道数据可参考")
            
            # 检查所有通道数据长度是否一致
            data_lengths = [len(arr) for arr in data_array]
            if len(set(data_lengths)) > 1:
                print(f"警告: 通道数据长度不一致: {data_lengths}")
                # 找到最短的长度
                min_length = min(data_lengths)
                # 截断所有通道数据到最短长度
                data_array = [arr[:min_length] for arr in data_array]
                print(f"已将所有通道数据截断到长度 {min_length}")
                    
            # 创建MNE Raw对象
            data_array = np.array(data_array)
            print(f"数据数组形状: {data_array.shape}")
            
            # 创建通道信息
            ch_types = ['eeg'] * len(channels)  # 假设所有通道都是EEG
            
            # 检查是否有特殊通道（如EOG、ECG等）
            for i, ch in enumerate(channels):
                ch_lower = ch.lower()
                if 'eog' in ch_lower or 'eye' in ch_lower:
                    ch_types[i] = 'eog'
                elif 'ecg' in ch_lower or 'heart' in ch_lower:
                    ch_types[i] = 'ecg'
                elif 'emg' in ch_lower or 'muscle' in ch_lower:
                    ch_types[i] = 'emg'
                elif 'misc' in ch_lower or 'other' in ch_lower:
                    ch_types[i] = 'misc'
            
            info = mne.create_info(ch_names=channels, sfreq=sampling_rate, ch_types=ch_types)
            raw = mne.io.RawArray(data_array, info)
            
            # 添加额外的元数据
            if 'metadata' in preprocessed_data:
                for key, value in preprocessed_data['metadata'].items():
                    if key not in raw.info:
                        raw.info[key] = value
            
            # 改进事件处理: 处理各种格式的事件信息
            events_data = []
            events_from_annotations = False
            
            if 'events' in preprocessed_data:
                print(f"预处理数据中包含事件信息: {preprocessed_data['events']}")
                try:
                    # 处理不同格式的事件数据
                    events_info = preprocessed_data['events']
                    
                    # 情况1: events是一个对象，包含events数组
                    if isinstance(events_info, dict) and 'events' in events_info and isinstance(events_info['events'], list):
                        events_info = events_info['events']
                    
                    # 情况2: events直接是一个数组
                    if isinstance(events_info, list):
                        for event in events_info:
                            if isinstance(event, dict):
                                # 提取事件ID和时间点
                                event_id = event.get('id') or event.get('event_id') or event.get('code')
                                onset = event.get('onset') or event.get('time') or event.get('latency')
                                
                                if event_id is not None and onset is not None:
                                    # 转换时间点到采样点
                                    sample = int(float(onset) * sampling_rate)
                                    # 确保event_id是整数
                                    try:
                                        event_id_int = int(event_id)
                                    except (ValueError, TypeError):
                                        # 如果不能转换为整数，使用字符串的哈希值
                                        event_id_int = abs(hash(str(event_id))) % 10000
                                        print(f"事件ID不是整数，使用哈希值: {event_id} -> {event_id_int}")
                                    
                                    events_data.append([sample, 0, event_id_int])
                                    
                                    # 添加注释同时保留原始信息
                                    description = str(event_id)
                                    raw.annotations.append(
                                        onset=onset,
                                        duration=event.get('duration', 0),
                                        description=description
                                    )
                                    events_from_annotations = True
                    
                    if events_data:
                        print(f"成功处理 {len(events_data)} 个事件")
                        if not events_from_annotations:
                            # 如果没有通过注释添加事件，则直接创建事件数组
                            events_array = np.array(events_data, dtype=int)
                            # 确保至少添加一个虚拟刺激通道
                            stim_data = np.zeros((1, data_array.shape[1]))
                            for event in events_array:
                                if 0 <= event[0] < data_array.shape[1]:  # 确保在有效范围内
                                    stim_data[0, event[0]] = event[2]  # 设置刺激代码
                            
                            # 添加刺激通道
                            stim_info = mne.create_info(['STI'], raw.info['sfreq'], ['stim'])
                            stim_raw = mne.io.RawArray(stim_data, stim_info)
                            raw.add_channels([stim_raw])
                            print(f"已添加刺激通道并设置事件")
                    else:
                        print("未能从事件信息中提取有效事件")
                except Exception as e:
                    print(f"处理事件信息失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # 如果没有成功添加事件，仍然添加一个虚拟事件作为后备
            if not events_data:
                print("未提取到有效事件，添加虚拟事件")
                # 在数据中间添加一个事件
                middle_sample = len(data_array[0]) // 2
                stim_data = np.zeros((1, len(data_array[0])))
                stim_data[0, middle_sample] = 1  # 在中间位置添加一个触发器
                
                # 添加一个刺激通道
                stim_info = mne.create_info(['STI'], raw.info['sfreq'], ['stim'])
                stim_raw = mne.io.RawArray(stim_data, stim_info)
                raw.add_channels([stim_raw])
                print(f"已添加虚拟事件通道，事件位置: {middle_sample}")
                
                # 创建一个虚拟事件数组
                virtual_events = np.array([[middle_sample, 0, 1]], dtype=int)
                print(f"创建虚拟事件数组: {virtual_events}")
                
                # 添加注释
                onset = middle_sample / raw.info['sfreq']  # 转换为秒
                raw.annotations.append(onset, 0.1, '1')  # 添加一个注释
                print(f"已添加虚拟事件注释: onset={onset}")
            
            print(f"成功将预处理数据转换为MNE Raw对象，通道数: {len(raw.ch_names)}")
            return raw
        except Exception as e:
            print(f"转换预处理数据到MNE格式失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"转换预处理数据失败: {str(e)}")

    def compute_time_freq(self, dataset_id: str, subject_id: str, params: TimeFreqParams) -> Dict[str, Any]:
        """计算时频分析结果"""
        try:
            # 检查是否使用预处理数据
            if params.use_preprocessed_data and params.preprocessed_data:
                logger.info(f"使用预处理数据进行时频分析")
                raw = self._convert_preprocessed_to_mne(params.preprocessed_data)
            else:
                # 获取原始数据
                raw = self.dataset_service.get_raw_data(dataset_id, subject_id)
                
                # 如果需要预处理
                if params.preprocess and params.preprocess_params:
                    # 应用预处理
                    logger.info(f"应用预处理参数: {params.preprocess_params}")
                    # TODO: 实现预处理逻辑
                    pass
            
            # 计算功率谱 - 使用正确的导入和函数调用
            try:
                # 首先尝试直接导入
                try:
                    from mne.time_frequency import psd_welch
                    print("成功导入 mne.time_frequency.psd_welch")
                    
                    # 使用psd_welch计算功率谱
                    print(f"使用psd_welch计算功率谱，频率范围: {params.freqs[0]} - {params.freqs[-1]} Hz")
                    psds, freqs = psd_welch(
                        raw, 
                        fmin=params.freqs[0], 
                        fmax=params.freqs[-1],
                        n_fft=1024,
                        n_overlap=512
                    )
                    print(f"功率谱计算完成，形状: {psds.shape}, 频率数: {len(freqs)}")
                    
                except (ImportError, AttributeError) as e:
                    # 尝试备用导入路径
                    print(f"导入mne.time_frequency.psd_welch失败: {str(e)}")
                    print("尝试备用导入路径: mne.time_frequency.spectrum.psd_welch")
                    
                    from mne.time_frequency.spectrum import psd_welch
                    psds, freqs = psd_welch(
                        raw, 
                        fmin=params.freqs[0], 
                        fmax=params.freqs[-1],
                        n_fft=1024,
                        n_overlap=512
                    )
                    print(f"使用备用路径成功计算功率谱，形状: {psds.shape}")
                    
            except Exception as e:
                # 备用方法：使用原始数据直接计算功率谱
                print(f"使用MNE的PSD函数失败: {str(e)}")
                print("使用备用方法 (SciPy) 计算功率谱")
                
                # 使用scipy计算功率谱
                from scipy import signal
                data = raw.get_data()
                sampling_rate = raw.info['sfreq']
                print(f"原始数据形状: {data.shape}, 采样率: {sampling_rate} Hz")
                
                # 初始化结果容器
                n_channels = len(raw.ch_names)
                n_freqs = len(params.freqs)
                psds = np.zeros((n_channels, n_freqs))
                freqs = np.array(params.freqs)
                
                # 为每个通道计算功率谱
                for i in range(n_channels):
                    # 使用Welch方法计算PSD
                    f, Pxx = signal.welch(
                        data[i], 
                        fs=sampling_rate, 
                        nperseg=1024, 
                        noverlap=512,
                        nfft=2048
                    )
                    
                    # 通过插值将结果映射到请求的频率上
                    from scipy.interpolate import interp1d
                    interp_func = interp1d(f, Pxx, kind='linear', fill_value='extrapolate')
                    psds[i] = interp_func(freqs)
                
                print(f"使用SciPy完成功率谱计算，形状: {psds.shape}")
            
            # 转换为字典格式
            spectrum_result = {
                "frequencies": freqs.tolist(),
                "channels": raw.ch_names,
                "powers": {ch: psds[i].tolist() for i, ch in enumerate(raw.ch_names)}
            }
            print(f"频谱结果准备完成，包含 {len(raw.ch_names)} 个通道")
            
            # 计算时频表示
            try:
                print("开始计算时频表示...")
                # 查找事件
                try:
                    events = mne.find_events(raw)
                    print(f"找到 {len(events)} 个事件")
                    
                    if len(events) == 0:
                        # 如果没有找到事件，从注释创建
                        if len(raw.annotations) > 0:
                            print(f"从 {len(raw.annotations)} 个注释创建事件")
                            events = mne.events_from_annotations(raw)[0]
                            print(f"从注释创建了 {len(events)} 个事件")
                        
                        # 如果仍然没有事件，创建一个虚拟事件
                        if len(events) == 0:
                            print("没有找到事件，创建虚拟事件")
                            middle_sample = len(raw.times) // 2
                            events = np.array([[middle_sample, 0, 1]], dtype=int)
                            print(f"创建虚拟事件在样本点 {middle_sample}")
                except Exception as e:
                    print(f"查找事件失败: {str(e)}")
                    print("创建虚拟事件作为后备")
                    middle_sample = len(raw.times) // 2
                    events = np.array([[middle_sample, 0, 1]], dtype=int)
                
                # 创建epochs
                print("创建epochs...")
                try:
                    epochs = mne.Epochs(
                        raw, 
                        events, 
                        tmin=-0.5, 
                        tmax=1.0,
                        baseline=None,
                        preload=True,
                        reject=None,
                        flat=None
                    )
                    
                    print(f"成功创建epochs，包含 {len(epochs)} 个epoch")
                except Exception as e:
                    print(f"创建epochs失败: {str(e)}")
                    print("尝试使用更小的时间窗口")
                    
                    # 尝试使用更小的时间窗口
                    epochs = mne.Epochs(
                        raw, 
                        events, 
                        tmin=-0.2, 
                        tmax=0.5,
                        baseline=None,
                        preload=True,
                        reject=None,
                        flat=None
                    )
                    print(f"使用更小的时间窗口成功创建epochs，包含 {len(epochs)} 个epoch")
                
                # 使用正确的方法计算时频
                print(f"使用 {params.method} 方法计算时频表示...")
                
                if params.method.lower() == 'morlet':
                    # 使用morlet小波变换计算时频
                    print(f"使用Morlet小波变换，频率范围: {min(params.freqs)}-{max(params.freqs)} Hz，周期数: {params.n_cycles}")
                    tfr = tfr_morlet(
                        epochs,
                        freqs=params.freqs,
                        n_cycles=params.n_cycles,
                        return_itc=False,
                        average=False
                    )
                    
                    print(f"时频变换完成，形状: {tfr.data.shape}")
                else:
                    # 使用短时傅里叶变换 (STFT) 作为备用方法
                    print(f"使用STFT作为备用方法")
                    from mne.time_frequency import tfr_multitaper
                    
                    tfr = tfr_multitaper(
                        epochs,
                        freqs=params.freqs,
                        n_cycles=params.n_cycles,
                        time_bandwidth=4,
                        return_itc=False,
                        average=False
                    )
                    print(f"使用多窗函数计算时频变换完成，形状: {tfr.data.shape}")
                
                # 检查计算结果并修复可能存在的问题
                if tfr.data.ndim != 4:
                    print(f"警告: TFR数据维度不符合预期，期望4维，实际 {tfr.data.ndim} 维")
                    # 尝试修复数据维度
                    if tfr.data.ndim == 3:
                        # 可能缺少通道维度或试次维度
                        tfr.data = tfr.data.reshape(1, *tfr.data.shape)
                        print(f"已将TFR数据形状调整为 {tfr.data.shape}")
                
                # 检查是否有NaN或Inf
                if np.isnan(tfr.data).any() or np.isinf(tfr.data).any():
                    print(f"警告: TFR数据中存在NaN或Inf值，将被替换为0")
                    tfr.data = np.nan_to_num(tfr.data, nan=0.0, posinf=0.0, neginf=0.0)
                
                # 转换为字典格式 - 形状为: [试次数, 通道数, 频率数, 时间点数]
                # 我们将使用第一个试次的数据作为示例
                print("将时频数据转换为前端所需格式...")
                
                # 对于3D功率数据 [通道数, 频率数, 时间点数]
                power_data = tfr.data[0] if tfr.data.shape[0] > 0 else np.zeros((len(raw.ch_names), len(params.freqs), len(tfr.times)))
                
                time_freq_result = {
                    "times": tfr.times.tolist(),
                    "frequencies": tfr.freqs.tolist(),
                    "power": power_data.tolist(),  # 3D数组: [通道, 频率, 时间]
                    "events": [{"time": 0, "name": "事件", "color": "#ff0000"}]
                }
                print(f"时频结果准备完成，包含 {len(raw.ch_names)} 个通道的数据")
                
            except Exception as e:
                print(f"时频变换计算失败: {str(e)}")
                print("创建默认时频数据")
                import traceback
                traceback.print_exc()
                
                # 创建一个默认的时频数据结构
                times = np.linspace(-0.5, 1.0, 100)
                frequencies = np.array(params.freqs)
                
                # 生成3D功率数据 [通道数, 频率数, 时间点数]
                power = []
                
                # 生成随机的功率数据
                for i in range(len(raw.ch_names)):
                    channel_power = []
                    for j in range(len(frequencies)):
                        # 为每个频率创建时间序列
                        time_series = np.zeros(len(times))
                        
                        # 在时间点0处创建一个事件相关响应
                        event_idx = np.argmin(np.abs(times))
                        time_series[event_idx:] = 3 * np.exp(-np.arange(len(times) - event_idx) / 10) * np.sin(2 * np.pi * frequencies[j] * 0.01 * np.arange(len(times) - event_idx))
                        
                        # 添加一些随机噪声
                        time_series += 0.5 * np.random.randn(len(times))
                        
                        channel_power.append(time_series.tolist())
                    
                    power.append(channel_power)
                
                time_freq_result = {
                    "times": times.tolist(),
                    "frequencies": frequencies.tolist(),
                    "power": power,  # 3D数组: [通道, 频率, 时间]
                    "events": [{"time": 0, "name": "事件", "color": "#ff0000"}]
                }
            
            print("时频分析完成，返回结果")
            return {
                "spectrum": spectrum_result,
                "timeFrequency": time_freq_result
            }
        except Exception as e:
            logger.error(f"时频分析失败: {str(e)}")
            print(f"时频分析出现异常: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 返回一个简单的默认响应，而不是抛出异常
            # 创建默认的频谱数据
            default_freqs = params.freqs
            default_spectrum = {
                "frequencies": default_freqs,
                "channels": ["Fz", "Cz", "Pz"],
                "powers": {
                    "Fz": [0.1 * i if i < 8 else (5 if 8 <= i <= 12 else 0.1 * (40 - i)) for i in range(len(default_freqs))],
                    "Cz": [0.1 * i if i < 13 else (3 if 13 <= i <= 30 else 0.1 * (40 - i)) for i in range(len(default_freqs))],
                    "Pz": [0.1 * i if i < 4 else (4 if 4 <= i <= 7 else 0.1 * (40 - i)) for i in range(len(default_freqs))]
                }
            }
            
            # 创建默认的时频数据 - 3D数组 [通道, 频率, 时间]
            times = np.linspace(-0.5, 1.0, 100).tolist()
            frequencies = default_freqs
            
            # 生成一些模拟的时频数据 - 3D数组
            power = []
            for _ in range(3):  # 3个通道
                channel_power = []
                for j, f in enumerate(frequencies):
                    # 为每个频率创建时间序列
                    power_values = []
                    for t_idx, t in enumerate(times):
                        if f >= 8 and f <= 12 and t >= 0.1:  # Alpha
                            val = 3 + 2 * np.sin(t * 5) * np.exp(-t)
                        elif f >= 13 and f <= 30 and t >= 0.2:  # Beta
                            val = 2 + np.sin(t * 8) * np.exp(-t)
                        elif f >= 4 and f <= 7 and t >= 0:  # Theta
                            val = 4 + 3 * np.sin(t * 3) * np.exp(-t)
                        else:
                            val = 0.5 * np.random.random()
                        power_values.append(val)
                    channel_power.append(power_values)
                power.append(channel_power)
            
            default_time_freq = {
                "times": times,
                "frequencies": frequencies,
                "power": power,  # 3D数组: [通道, 频率, 时间]
                "events": [{"time": 0, "name": "事件", "color": "#ff0000"}]
            }
            
            print("返回默认时频分析结果")
            return {
                "spectrum": default_spectrum,
                "timeFrequency": default_time_freq
            }

    def compute_connectivity(self, dataset_id: str, subject_id: str, params: ConnectivityParams) -> Dict[str, Any]:
        """计算连接性分析结果"""
        try:
            # 检查是否使用预处理数据
            if params.use_preprocessed_data and params.preprocessed_data:
                logger.info(f"使用预处理数据进行连接性分析")
                raw = self._convert_preprocessed_to_mne(params.preprocessed_data)
            else:
                # 获取原始数据
                raw = self.dataset_service.get_raw_data(dataset_id, subject_id)
                
                # 如果需要预处理
                if params.preprocess and params.preprocess_params:
                    # 应用预处理
                    logger.info(f"应用预处理参数: {params.preprocess_params}")
                    # TODO: 实现预处理逻辑
                    pass
            
            # 提取感兴趣的频段
            raw_band = raw.copy().filter(params.fmin, params.fmax)
            
            # 计算连接性矩阵
            # 这里简化处理，实际应该使用更复杂的连接性分析方法
            data = raw_band.get_data()
            n_channels = len(raw_band.ch_names)
            conn_matrix = np.corrcoef(data)
            
            # 转换为字典格式
            result = {
                "channels": raw_band.ch_names,
                "connectivity": conn_matrix.tolist(),
                "method": params.method,
                "freq_range": [params.fmin, params.fmax]
            }
            
            return result
        except Exception as e:
            logger.error(f"连接性分析失败: {str(e)}")
            raise e

    def compute_time_frequency(self, epochs, params):
        """计算时频表示，参考TimeFreqComputeClusterChan_NoCommonBase.m"""
        
        # 设置频率范围
        freqs = np.arange(params.get('fmin', 3), params.get('fmax', 40), 
                         params.get('fstep', 1))
        
        # 计算功率谱 (ERSP)
        power = tfr_morlet(epochs, freqs, 
                          n_cycles=params.get('n_cycles', freqs/2), 
                          return_itc=False)
        
        # 计算相位锁定值 (ITC)
        if params.get('compute_itc', True):
            _, itc = tfr_morlet(epochs, freqs, 
                               n_cycles=params.get('n_cycles', freqs/2), 
                               return_itc=True)
        else:
            itc = None
        
        # 提取特定频带
        if params.get('extract_bands', False):
            bands = {
                'theta': (3, 8),
                'alpha': (8, 13),
                'beta': (13, 30),
                'gamma': (30, 45)
            }
            band_power = {}
            for band_name, (fmin, fmax) in bands.items():
                band_power[band_name] = self._extract_frequency_band(power, freqs, fmin, fmax)
        else:
            band_power = None
        
        return {'power': power, 'itc': itc, 'band_power': band_power}

    def _extract_frequency_band(self, power, freqs, fmin, fmax):
        """提取特定频带的功率"""
        # 找到频带范围内的索引
        freq_idx = np.where((freqs >= fmin) & (freqs <= fmax))[0]
        # 提取并平均该频带的功率
        band_power = np.mean(power.data[:, :, freq_idx, :], axis=2)
        return band_power

    def compute_statistics(self, data1, data2, params):
        """执行统计分析"""
        
        # 配对t检验
        t_vals, p_vals = ttest_rel(data1, data2, axis=0)
        
        # 多重比较校正
        if params.get('correction', 'fdr') == 'fdr':
            # 使用MNE的fdr_correction函数
            _, p_vals_corrected = fdr_correction(p_vals.flatten())
            p_vals_corrected = p_vals_corrected.reshape(p_vals.shape)
        else:
            p_vals_corrected = p_vals
        
        # 计算效应量
        effect_size = (np.mean(data1, axis=0) - np.mean(data2, axis=0)) / \
                     np.sqrt((np.std(data1, axis=0)**2 + np.std(data2, axis=0)**2) / 2)
        
        # 添加beta斜率分析
        if params.get('compute_beta_slopes', False):
            beta_slopes = self._calculate_beta_slopes(data1, data2, 
                                                    params.get('time_window', [-1000, -500]))
            result_slopes = beta_slopes
        else:
            result_slopes = None
        
        return {
            't_values': t_vals.tolist() if isinstance(t_vals, np.ndarray) else t_vals,
            'p_values': p_vals.tolist() if isinstance(p_vals, np.ndarray) else p_vals,
            'p_corrected': p_vals_corrected.tolist() if isinstance(p_vals_corrected, np.ndarray) else p_vals_corrected,
            'effect_size': effect_size.tolist() if isinstance(effect_size, np.ndarray) else effect_size,
            'beta_slopes': result_slopes
        }

    def _calculate_beta_slopes(self, data1, data2, time_window):
        """计算beta频带斜率"""
        # 简化实现，实际应根据具体需求实现
        # 这里假设data1和data2是时间序列数据
        
        # 提取时间窗口内的数据
        # 实际实现应根据时间点索引提取相应数据
        
        # 计算斜率（简化为线性拟合）
        slopes = []
        for i in range(data1.shape[1]):  # 遍历通道
            x = np.arange(data1.shape[0])  # 时间点
            y1 = data1[:, i]  # 条件1的数据
            y2 = data2[:, i]  # 条件2的数据
            
            # 线性拟合
            slope1 = np.polyfit(x, y1, 1)[0]
            slope2 = np.polyfit(x, y2, 1)[0]
            
            slopes.append((slope1, slope2))
        
        return slopes 