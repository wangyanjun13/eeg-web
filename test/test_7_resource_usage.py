#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EEG-Web系统资源利用率时序分布图

此脚本用于生成EEG-Web系统在不同工作负载下的资源利用率时序分布图，
展示系统的CPU和内存使用情况。
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def create_resource_chart(data=None):
    """
    创建资源利用率时序分布图
    
    参数:
        data: 包含资源使用数据的字典，如果为None则尝试从文件加载
    """
    # 如果没有提供数据，尝试从文件加载
    if data is None:
        data_file = Path('./testing_data/resource_usage.json')
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # 创建模拟数据
            print("未找到数据文件，使用模拟数据")
            
            # 时间点（分钟）
            time_points = np.arange(0, 120, 2).tolist()  # 0到118分钟，每2分钟一个采样点
            
            # CPU使用率数据模拟
            cpu_base = np.zeros_like(time_points, dtype=float)
            for i, t in enumerate(time_points):
                if t < 30:
                    # 启动阶段
                    cpu_base[i] = 35 + 10 * np.sin(t/5)
                elif t < 60:
                    # 休眠期
                    cpu_base[i] = 15 + 5 * np.sin(t/8)
                elif t < 90:
                    # 密集处理期
                    cpu_base[i] = 70 + 15 * np.sin(t/4)
                else:
                    # 平稳运行期
                    cpu_base[i] = 40 + 10 * np.sin(t/6)
            
            # 添加随机波动
            np.random.seed(42)
            cpu_usage = np.clip(cpu_base + np.random.normal(0, 4, size=len(time_points)), 0, 100).tolist()
            
            # 内存使用率数据模拟
            mem_base = np.zeros_like(time_points, dtype=float)
            for i, t in enumerate(time_points):
                # 基础内存使用率
                mem_base[i] = 30
                
                # 随工作负载阶段性增加
                if t >= 20:
                    mem_base[i] += 10  # 加载第一个数据集
                    
                if t >= 45:
                    mem_base[i] += 15  # 加载更多数据和模型
                    
                if t >= 65:
                    mem_base[i] += 25  # ICA和时频分析增加内存需求
                    
                # 模拟周期性垃圾回收
                gc_trigger = (t % 15 == 0) and (t > 0)
                if gc_trigger and t > 60:  # 在高负载后触发GC
                    mem_base[i] -= 10
            
            # 添加随机波动 
            mem_usage = np.clip(mem_base + np.random.normal(0, 2, size=len(time_points)), 0, 100).tolist()
            
            data = {
                "time_points": time_points,
                "cpu_usage": cpu_usage,
                "mem_usage": mem_usage
            }
    
    # 提取数据
    time_points = np.array(data["time_points"])
    cpu_usage = np.array(data["cpu_usage"])
    mem_usage = np.array(data["mem_usage"])
    
    # 创建时间戳
    start_time = datetime.now() - timedelta(minutes=time_points[-1])
    timestamps = [start_time + timedelta(minutes=t) for t in time_points]
    
    # 创建图形
    plt.figure(figsize=(15, 12), dpi=100)
    
    # 定义工作阶段
    phases = [
        {"name": "启动阶段", "start": 0, "end": 30, "color": "lightblue"},
        {"name": "数据加载", "start": 30, "end": 60, "color": "lightyellow"},
        {"name": "密集处理", "start": 60, "end": 90, "color": "lightcoral"},
        {"name": "平稳运行", "start": 90, "end": 120, "color": "lightgreen"}
    ]
    
    # CPU使用率图
    ax1 = plt.subplot(211)
    
    # 绘制工作阶段背景
    for phase in phases:
        ax1.axvspan(start_time + timedelta(minutes=phase["start"]), 
                   start_time + timedelta(minutes=phase["end"]), 
                   alpha=0.3, color=phase["color"], label=phase["name"])
    
    # 绘制CPU使用率曲线
    ax1.plot(timestamps, cpu_usage, 'b-', linewidth=2, label='CPU使用率')
    
    # 添加移动平均线
    window = 5  # 移动平均窗口大小
    if len(cpu_usage) > window:
        cpu_ma = np.convolve(cpu_usage, np.ones(window)/window, mode='valid')
        ma_timestamps = timestamps[window-1:]
        ax1.plot(ma_timestamps, cpu_ma, 'r--', linewidth=1.5, label=f'{window}点移动平均')
    
    # 标记峰值和谷值
    peak_idx = np.argmax(cpu_usage)
    valley_idx = np.argmin(cpu_usage)
    
    ax1.plot(timestamps[peak_idx], cpu_usage[peak_idx], 'ro', markersize=8)
    ax1.annotate(f'峰值: {cpu_usage[peak_idx]:.1f}%', 
                xy=(timestamps[peak_idx], cpu_usage[peak_idx]), 
                xytext=(timestamps[peak_idx], cpu_usage[peak_idx]+10),
                arrowprops=dict(facecolor='red', shrink=0.05))
    
    ax1.plot(timestamps[valley_idx], cpu_usage[valley_idx], 'go', markersize=8)
    ax1.annotate(f'谷值: {cpu_usage[valley_idx]:.1f}%', 
                xy=(timestamps[valley_idx], cpu_usage[valley_idx]), 
                xytext=(timestamps[valley_idx], cpu_usage[valley_idx]-15),
                arrowprops=dict(facecolor='green', shrink=0.05))
    
    # 设置CPU图属性
    ax1.set_title("CPU使用率随时间变化", fontsize=14)
    ax1.set_ylabel("CPU使用率(%)", fontsize=12)
    ax1.set_ylim(0, 100)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    # 只在第一个子图中显示图例
    handles, labels = ax1.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax1.legend(by_label.values(), by_label.keys(), loc='upper right')
    
    # 内存使用率图
    ax2 = plt.subplot(212, sharex=ax1)
    
    # 绘制工作阶段背景
    for phase in phases:
        ax2.axvspan(start_time + timedelta(minutes=phase["start"]), 
                   start_time + timedelta(minutes=phase["end"]), 
                   alpha=0.3, color=phase["color"])
    
    # 绘制内存使用率曲线
    ax2.plot(timestamps, mem_usage, 'g-', linewidth=2, label='内存使用率')
    
    # 添加移动平均线
    if len(mem_usage) > window:
        mem_ma = np.convolve(mem_usage, np.ones(window)/window, mode='valid')
        ax2.plot(ma_timestamps, mem_ma, 'r--', linewidth=1.5, label=f'{window}点移动平均')
    
    # 标记内存使用的关键点
    # 找到内存使用明显变化的点
    mem_diff = np.diff(mem_usage)
    change_points = np.where(np.abs(mem_diff) > 5)[0]
    
    for i in change_points:
        if mem_diff[i] > 0:
            label = "增加"
            color = 'red'
            offset = 10
        else:
            label = "减少"
            color = 'green'
            offset = -10
        
        ax2.plot(timestamps[i+1], mem_usage[i+1], 'o', color=color, markersize=6)
        ax2.annotate(f'{label}: {abs(mem_diff[i]):.1f}%', 
                    xy=(timestamps[i+1], mem_usage[i+1]), 
                    xytext=(timestamps[i+1], mem_usage[i+1]+offset),
                    arrowprops=dict(facecolor=color, shrink=0.05),
                    fontsize=8)
    
    # 设置内存图属性
    ax2.set_title("内存使用率随时间变化", fontsize=14)
    ax2.set_xlabel("时间", fontsize=12)
    ax2.set_ylabel("内存使用率(%)", fontsize=12)
    ax2.set_ylim(0, 100)
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend(loc='upper right')
    
    # 设置整体标题
    plt.suptitle("EEG-Web系统资源利用率时序分布图", fontsize=16, fontweight='bold')
    
    # 添加说明文本
    description = """
    图表展示了系统在不同工作阶段的CPU和内存使用情况。
    蓝色区域: 启动阶段 | 黄色区域: 数据加载 | 红色区域: 密集处理 | 绿色区域: 平稳运行
    红色虚线表示移动平均值，可以更清晰地观察趋势变化。
    """
    plt.figtext(0.5, 0.01, description, ha='center', fontsize=12, 
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.5))
    
    # 保存图表
    results_dir = Path('./testing_results')
    results_dir.mkdir(parents=True, exist_ok=True)
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.savefig(results_dir / '图5.9_资源利用率.png', dpi=300)
    plt.close()
    
    # 计算资源使用统计信息
    stats = {
        "cpu": {
            "mean": np.mean(cpu_usage),
            "max": np.max(cpu_usage),
            "min": np.min(cpu_usage),
            "std": np.std(cpu_usage)
        },
        "memory": {
            "mean": np.mean(mem_usage),
            "max": np.max(mem_usage),
            "min": np.min(mem_usage),
            "std": np.std(mem_usage)
        },
        "phases": {}
    }
    
    # 计算各阶段的资源使用情况
    for phase in phases:
        start_idx = np.where(time_points >= phase["start"])[0][0]
        end_idx = np.where(time_points <= phase["end"])[0][-1]
        
        phase_cpu = cpu_usage[start_idx:end_idx+1]
        phase_mem = mem_usage[start_idx:end_idx+1]
        
        stats["phases"][phase["name"]] = {
            "cpu": {
                "mean": np.mean(phase_cpu),
                "max": np.max(phase_cpu),
                "std": np.std(phase_cpu)
            },
            "memory": {
                "mean": np.mean(phase_mem),
                "max": np.max(phase_mem),
                "std": np.std(phase_mem)
            }
        }
    
    return stats

if __name__ == "__main__":
    stats = create_resource_chart()
    
    print("资源使用分析结果:")
    print(f"CPU平均使用率: {stats['cpu']['mean']:.1f}%, 最大值: {stats['cpu']['max']:.1f}%, 标准差: {stats['cpu']['std']:.1f}%")
    print(f"内存平均使用率: {stats['memory']['mean']:.1f}%, 最大值: {stats['memory']['max']:.1f}%, 标准差: {stats['memory']['std']:.1f}%")
    
    print("\n各阶段资源使用情况:")
    for phase_name, phase_stats in stats["phases"].items():
        print(f"\n{phase_name}:")
        print(f"  CPU平均: {phase_stats['cpu']['mean']:.1f}%, 最大值: {phase_stats['cpu']['max']:.1f}%")
        print(f"  内存平均: {phase_stats['memory']['mean']:.1f}%, 最大值: {phase_stats['memory']['max']:.1f}%") 