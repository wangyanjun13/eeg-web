import mne
from typing import Dict, Any
from app.models.data_analysis import ERPParams, TimeFreqParams, ConnectivityParams
import numpy as np
from mne.time_frequency import tfr_morlet
from scipy.stats import ttest_rel
from mne.stats import fdr_correction

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
        """计算ERP"""
        # 获取原始数据
        raw = self.dataset_service._read_eeg_file(dataset_id, subject_id)
        
        # 如果需要预处理，可以在这里调用预处理服务
        # 但不直接在构造函数中依赖它，而是作为参数传入
        if params.preprocess:
            # 这里可以通过参数传入预处理服务实例
            # preprocess_service.preprocess_eeg(raw, params.preprocess_params)
            pass
            
        # ERP分析实现
        return {"status": "not implemented"}

    def compute_time_freq(self, dataset_id: str, subject_id: str, params: TimeFreqParams) -> Dict[str, Any]:
        """计算时频图"""
        raw = self.dataset_service._read_eeg_file(dataset_id, subject_id)
        # 时频分析实现
        return {"status": "not implemented"}

    def compute_connectivity(self, dataset_id: str, subject_id: str, params: ConnectivityParams) -> Dict[str, Any]:
        """计算连接性"""
        raw = self.dataset_service._read_eeg_file(dataset_id, subject_id)
        # 连接性分析实现
        return {"status": "not implemented"}

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