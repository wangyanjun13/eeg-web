#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EEG-Web多模态分析可视化示例图

此脚本用于生成EEG-Web系统多模态分析的可视化示例图，
展示系统在时域、频域、时频域和空间域分析的能力。
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
from matplotlib.colors import LinearSegmentedColormap

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def create_multimodal_visualization(data=None):
    """
    创建EEG-Web多模态分析可视化示例图
    
    参数:
        data: 包含多模态分析数据的字典，如果为None则尝试从文件加载
    """
    # 如果没有提供数据，尝试从文件加载
    if data is None:
        data_file = Path('./testing_data/multimodal_analysis.json')
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # 创建模拟数据
            print("未找到数据文件，使用模拟数据")
            
            # 时域数据 - 模拟ERP波形
            times = np.linspace(-0.2, 0.8, 200)
            time_domain = {
                "times": times.tolist(),
                "signals": {
                    "Fz": (2*np.exp(-(times-0.3)**2/0.02) - 
                           0.8*np.exp(-(times-0.15)**2/0.01) + 
                           0.2*np.random.randn(len(times))).tolist(),
                    "Cz": (3*np.exp(-(times-0.35)**2/0.015) - 
                           0.5*np.exp(-(times-0.1)**2/0.01) + 
                           0.2*np.random.randn(len(times))).tolist(),
                    "Pz": (3.5*np.exp(-(times-0.3)**2/0.01) - 
                           0.3*np.exp(-(times-0.2)**2/0.02) + 
                           0.2*np.random.randn(len(times))).tolist()
                }
            }
            
            # 频域数据 - 模拟功率谱
            frequencies = np.linspace(0, 50, 100)
            frequency_domain = {
                "frequencies": frequencies.tolist(),
                "powers": {
                    "Fz": (5*np.exp(-(frequencies-6)**2/8) + 
                           3*np.exp(-(frequencies-10)**2/4) + 
                           1.5*np.exp(-(frequencies-20)**2/30) + 0.1).tolist(),
                    "Cz": (3*np.exp(-(frequencies-6)**2/10) + 
                           6*np.exp(-(frequencies-10)**2/5) + 
                           2*np.exp(-(frequencies-20)**2/20) + 0.1).tolist(),
                    "Pz": (2*np.exp(-(frequencies-5)**2/12) + 
                           8*np.exp(-(frequencies-10)**2/4) + 
                           1*np.exp(-(frequencies-22)**2/50) + 0.1).tolist()
                }
            }
            
            # 时频域数据 - 模拟时频图
            time_freq_times = np.linspace(-0.2, 0.8, 50)
            time_freq_freqs = np.linspace(1, 40, 40)
            time_freq_data = np.zeros((len(time_freq_freqs), len(time_freq_times)))
            
            # 添加时变的频率活动
            for i, t in enumerate(time_freq_times):
                # Alpha活动 (8-12 Hz)
                if -0.1 < t < 0.2:
                    alpha_idx = np.where((time_freq_freqs >= 8) & (time_freq_freqs <= 12))[0]
                    time_freq_data[alpha_idx, i] += 3 * np.exp(-(t-0.05)**2/0.01)
                
                # Beta活动 (15-25 Hz)
                if 0.2 < t < 0.5:
                    beta_idx = np.where((time_freq_freqs >= 15) & (time_freq_freqs <= 25))[0]
                    time_freq_data[beta_idx, i] += 2 * np.exp(-(t-0.35)**2/0.02)
                
                # Theta活动 (4-7 Hz)
                if 0.4 < t < 0.7:
                    theta_idx = np.where((time_freq_freqs >= 4) & (time_freq_freqs <= 7))[0]
                    time_freq_data[theta_idx, i] += 2.5 * np.exp(-(t-0.55)**2/0.015)
            
            # 添加噪声
            time_freq_data += 0.2 * np.random.randn(*time_freq_data.shape)
            time_freq_data = np.maximum(time_freq_data, 0)  # 确保值非负
            
            time_frequency = {
                "times": time_freq_times.tolist(),
                "frequencies": time_freq_freqs.tolist(),
                "power": time_freq_data.tolist()
            }
            
            # 空间域数据 - 模拟头皮地形图
            channel_names = ['Fp1', 'Fpz', 'Fp2', 'F7', 'F3', 'Fz', 'F4', 'F8', 
                           'T7', 'C3', 'Cz', 'C4', 'T8', 'P7', 'P3', 'Pz', 
                           'P4', 'P8', 'O1', 'Oz', 'O2']
            
            # 模拟Alpha波功率分布
            np.random.seed(42)
            base_power = 0.5 + 0.5 * np.random.rand(len(channel_names))
            
            # 增强枕区Alpha波
            occipital_idx = [channel_names.index(ch) for ch in ['O1', 'Oz', 'O2', 'P7', 'P3', 'Pz', 'P4', 'P8']]
            for idx in occipital_idx:
                base_power[idx] += 1.0 + 0.5 * np.random.rand()
            
            spatial = {
                "channel_names": channel_names,
                "alpha_power": base_power.tolist()
            }
            
            data = {
                "time_domain": time_domain,
                "frequency_domain": frequency_domain,
                "time_frequency": time_frequency,
                "spatial": spatial
            }
    
    # 创建图形
    plt.figure(figsize=(16, 12), dpi=100)
    gs = gridspec.GridSpec(2, 2, width_ratios=[1, 1], height_ratios=[1, 1])
    
    # 1. 时域分析 - ERP波形
    ax1 = plt.subplot(gs[0, 0])
    for channel, signal in data["time_domain"]["signals"].items():
        ax1.plot(data["time_domain"]["times"], signal, label=channel, linewidth=2)
    
    ax1.set_title("时域分析 - ERP波形", fontsize=14)
    ax1.set_xlabel("时间(s)", fontsize=12)
    ax1.set_ylabel("振幅(μV)", fontsize=12)
    ax1.axvline(x=0, color='k', linestyle='--', alpha=0.5)  # 刺激呈现时刻
    ax1.axhline(y=0, color='k', linestyle='-', alpha=0.2)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(fontsize=10)
    
    # 添加P300标记
    p300_time = 0.3  # P300通常出现在300ms
    p300_amp = max(data["time_domain"]["signals"]["Pz"][
        np.argmin(np.abs(np.array(data["time_domain"]["times"]) - p300_time))
    ], 3)  # 使用Pz的实际值或默认值
    
    ax1.annotate('P300', xy=(p300_time, p300_amp), xytext=(p300_time+0.1, p300_amp+1),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8),
                fontsize=10)
    
    # 2. 频域分析 - 功率谱
    ax2 = plt.subplot(gs[0, 1])
    for channel, power in data["frequency_domain"]["powers"].items():
        ax2.plot(data["frequency_domain"]["frequencies"], power, label=channel, linewidth=2)
    
    ax2.set_title("频域分析 - 功率谱", fontsize=14)
    ax2.set_xlabel("频率(Hz)", fontsize=12)
    ax2.set_ylabel("功率(dB)", fontsize=12)
    ax2.set_xlim(0, 40)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(fontsize=10)
    
    # 添加频段标记
    freq_bands = {
        'δ': (1, 4),
        'θ': (4, 8),
        'α': (8, 13),
        'β': (13, 30),
        'γ': (30, 40)
    }
    
    colors = ['#8B4513', '#228B22', '#FF8C00', '#4169E1', '#800080']
    for i, (band, (fmin, fmax)) in enumerate(freq_bands.items()):
        ax2.axvspan(fmin, fmax, color=colors[i], alpha=0.2)
        ax2.text((fmin+fmax)/2, ax2.get_ylim()[1]*0.9, band, 
                 ha='center', fontsize=12, color=colors[i], fontweight='bold')
    
    # 3. 时频分析 - 时频图
    ax3 = plt.subplot(gs[1, 0])
    
    # 获取时频数据
    if "time_frequency" in data:
        times = np.array(data["time_frequency"]["times"])
        freqs = np.array(data["time_frequency"]["frequencies"])
        tf_power = np.array(data["time_frequency"]["power"])
        
        # 创建自定义颜色映射
        cmap = LinearSegmentedColormap.from_list('eeg_cmap', ['#FFFFFF', '#FFF7BC', '#FEC44F', '#EC7014', '#662506'])
        
        # 绘制时频图
        im = ax3.contourf(times, freqs, tf_power, 40, cmap=cmap)
        plt.colorbar(im, ax=ax3, label='功率(dB)')
        
        ax3.set_title("时频分析 - 时频图(Cz)", fontsize=14)
        ax3.set_xlabel("时间(s)", fontsize=12)
        ax3.set_ylabel("频率(Hz)", fontsize=12)
        ax3.axvline(x=0, color='k', linestyle='--', alpha=0.5)  # 刺激呈现时刻
        
        # 标记频段
        for band, (fmin, fmax) in freq_bands.items():
            ax3.axhspan(fmin, fmax, color='none', edgecolor='k', linestyle='--', alpha=0.5)
            ax3.text(-0.18, (fmin+fmax)/2, band, ha='center', fontsize=10, 
                     color='k', fontweight='bold')
    else:
        ax3.text(0.5, 0.5, '时频数据不可用', ha='center', va='center', fontsize=14)
    
    # 4. 空间分析 - 头皮地形图
    ax4 = plt.subplot(gs[1, 1])
    
    if "spatial" in data:
        # 简化的头皮地形图可视化
        # 实际应用中应使用专业的头皮地形图绘制库
        
        # 定义电极位置（简化的2D位置）
        positions = {
            'Fp1': (-0.2, 0.9), 'Fpz': (0, 0.9), 'Fp2': (0.2, 0.9),
            'F7': (-0.6, 0.6), 'F3': (-0.3, 0.6), 'Fz': (0, 0.6), 'F4': (0.3, 0.6), 'F8': (0.6, 0.6),
            'T7': (-0.8, 0), 'C3': (-0.4, 0), 'Cz': (0, 0), 'C4': (0.4, 0), 'T8': (0.8, 0),
            'P7': (-0.6, -0.6), 'P3': (-0.3, -0.6), 'Pz': (0, -0.6), 'P4': (0.3, -0.6), 'P8': (0.6, -0.6),
            'O1': (-0.2, -0.9), 'Oz': (0, -0.9), 'O2': (0.2, -0.9)
        }
        
        # 绘制头部轮廓
        circle = plt.Circle((0, 0), 1, fill=False, edgecolor='black', linewidth=2)
        ax4.add_patch(circle)
        
        # 绘制鼻子和耳朵标记
        ax4.plot([0, 0], [1, 1.1], 'k-', linewidth=2)  # 鼻子
        ax4.plot([-1.1, -1], [0, 0], 'k-', linewidth=2)  # 左耳
        ax4.plot([1, 1.1], [0, 0], 'k-', linewidth=2)  # 右耳
        
        # 获取电极功率值
        channel_names = data["spatial"]["channel_names"]
        power_values = data["spatial"]["alpha_power"]
        
        # 绘制电极点和功率值
        norm = plt.Normalize(min(power_values), max(power_values))
        cmap = plt.cm.get_cmap('jet')
        
        for i, channel in enumerate(channel_names):
            if channel in positions:
                x, y = positions[channel]
                color = cmap(norm(power_values[i]))
                ax4.plot(x, y, 'o', markersize=12, markerfacecolor=color, markeredgecolor='black')
                ax4.text(x, y+0.05, channel, ha='center', va='bottom', fontsize=8)
        
        # 添加颜色条
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=ax4, label='Alpha波功率(dB)')
        
        ax4.set_title("空间分析 - Alpha波功率分布", fontsize=14)
    else:
        ax4.text(0.5, 0.5, '空间数据不可用', ha='center', va='center', fontsize=14)
    
    ax4.set_xlim(-1.2, 1.2)
    ax4.set_ylim(-1.2, 1.2)
    ax4.axis('off')
    
    # 设置整体标题
    plt.suptitle("EEG多模态分析可视化示例", fontsize=18, fontweight='bold')
    
    # 保存图表
    results_dir = Path('./testing_results')
    results_dir.mkdir(parents=True, exist_ok=True)
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(results_dir / '图5.5_多模态分析.png', dpi=300)
    plt.close()
    
    return True

if __name__ == "__main__":
    create_multimodal_visualization()
    print("多模态分析可视化图已生成") 