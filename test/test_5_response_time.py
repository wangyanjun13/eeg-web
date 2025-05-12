#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EEG-Web系统响应时间分布热力图

此脚本用于生成EEG-Web系统在不同操作和硬件配置下的响应时间分布热力图，
展示系统的响应性能。
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def create_heatmap(data=None):
    """
    创建系统响应时间分布热力图
    
    参数:
        data: 包含响应时间数据的字典，如果为None则尝试从文件加载
    """
    # 如果没有提供数据，尝试从文件加载
    if data is None:
        data_file = Path('./testing_data/response_time.json')
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # 创建模拟数据
            print("未找到数据文件，使用模拟数据")
            operations = ['数据加载', '基础滤波', 'ICA处理', '时频分析', 
                         '头皮地形图', '连通性分析', '3D可视化', '文件导出']
            configs = ['低配', '中配', '高配']
            
            # 模拟响应时间数据（秒）
            base_times = np.array([
                [4.2, 2.8, 1.6],  # 数据加载
                [2.5, 1.4, 0.8],  # 基础滤波
                [9.8, 5.7, 3.2],  # ICA处理
                [7.2, 4.1, 2.3],  # 时频分析
                [2.4, 1.5, 0.9],  # 头皮地形图
                [5.6, 3.2, 1.8],  # 连通性分析  
                [13.5, 7.8, 4.2],  # 3D可视化
                [3.8, 2.1, 1.2]   # 文件导出
            ])
            
            # 添加±15%偏差模拟真实世界波动
            np.random.seed(42)
            noise = base_times * np.random.uniform(-0.15, 0.15, base_times.shape)
            response_data = (base_times + noise).tolist()
            
            data = {
                "operations": operations,
                "configs": configs,
                "data": response_data
            }
    
    # 提取数据
    operations = data["operations"]
    configs = data["configs"]
    response_data = np.array(data["data"])
    
    # 创建图形
    plt.figure(figsize=(14, 10), dpi=100)
    
    # 设置seaborn样式
    sns.set_style("white")
    
    # 创建掩码用于突出显示差异
    mask = np.zeros_like(response_data, dtype=bool)
    
    # 创建热力图
    ax = sns.heatmap(response_data, annot=True, fmt=".2f", cmap="YlGnBu_r",
                 xticklabels=configs, yticklabels=operations,
                 linewidths=0.5, linecolor='white',
                 cbar_kws={'label': '响应时间(秒)'})
    
    # 计算改进百分比
    improvement = np.zeros_like(response_data)
    for i in range(len(operations)):
        for j in range(len(configs)-1):
            improvement[i,j] = ((response_data[i,j] - response_data[i,j+1]) / response_data[i,j]) * 100
    
    # 添加改进百分比标注
    for i in range(len(operations)):
        for j in range(len(configs)-1):
            plt.text(j+0.5, i+0.85, f'↓{improvement[i,j]:.1f}%', 
                    ha='center', va='center', color='white', fontsize=9,
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='green', alpha=0.7))
    
    # 计算从低配到高配的平均改进百分比
    avg_improvement = np.mean(((response_data[:,0] - response_data[:,-1]) / response_data[:,0]) * 100)
    
    # 设置图表属性
    plt.title("EEG-Web系统响应时间分布热力图", fontsize=16)
    plt.xlabel("硬件配置", fontsize=14)
    plt.ylabel("操作", fontsize=14)
    
    # 添加描述文本
    description = "响应时间单位：秒\n绿色标签表示与左侧配置相比的性能提升百分比"
    plt.figtext(0.5, 0.02, description, ha='center', fontsize=12, 
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.5))
    
    # 添加平均性能提升文本
    plt.figtext(0.5, 0.95, f"从低配到高配平均性能提升: {avg_improvement:.1f}%", 
                ha='center', fontsize=14, bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.5))
    
    # 保存图表
    results_dir = Path('./testing_results')
    results_dir.mkdir(parents=True, exist_ok=True)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.92])
    plt.savefig(results_dir / '图5.7_响应时间热力图.png', dpi=300)
    plt.close()
    
    return {
        "avg_improvement": avg_improvement,
        "improvement_by_operation": {op: ((response_data[i,0] - response_data[i,-1]) / response_data[i,0]) * 100 
                                  for i, op in enumerate(operations)}
    }

if __name__ == "__main__":
    results = create_heatmap()
    
    print("响应时间分析结果:")
    print(f"从低配到高配平均性能提升: {results['avg_improvement']:.1f}%")
    print("\n各操作性能提升:")
    for op, imp in results["improvement_by_operation"].items():
        print(f"{op}: {imp:.1f}%") 