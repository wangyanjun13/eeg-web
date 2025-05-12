#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EEG-Web系统性能数据收集与可视化脚本

此脚本从EEG-Web系统API获取实际性能数据，并生成各种可视化图表。
"""

import os
import sys
import json
import time
import datetime
import requests
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 配置
class Config:
    # API配置
    API_BASE_URL = "http://localhost:8000"  # 请根据实际情况修改
    
    # 结果保存路径
    RESULTS_DIR = "./testing_results"
    DATA_DIR = "./testing_data"
    
    # 超时设置（秒）
    TIMEOUT = 30

# 确保结果目录存在
def ensure_dir(directory):
    Path(directory).mkdir(parents=True, exist_ok=True)

# API客户端
class APIClient:
    def __init__(self, base_url=Config.API_BASE_URL, timeout=Config.TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
    
    def get(self, endpoint):
        """发送GET请求到指定端点"""
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"请求API: {url}")
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            
            # 检查响应格式 - 处理APIResponse格式
            if "data" in result:
                # 新的APIResponse格式
                if result.get("status") == "success" or result.get("message"):
                    return result.get("data")
            
            # 返回整个响应
            return result
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            return None
    
    def check_health(self):
        """检查API健康状态"""
        try:
            response = self.get("/health")
            return response is not None and response.get("status") == "healthy"
        except:
            return False

# 数据收集和可视化函数
def collect_mne_comparison_data(api_client):
    """收集MNE对比数据"""
    print("收集MNE对比数据...")
    data = api_client.get("/api/system/mne-comparison")
    
    if data:
        # 保存数据
        ensure_dir(Config.DATA_DIR)
        with open(f"{Config.DATA_DIR}/mne_comparison.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 生成可视化
        generate_mne_comparison_chart(data)
        return True
    else:
        print("无法获取MNE对比数据，请检查API是否可用")
        return False

def generate_mne_comparison_chart(data):
    """生成MNE对比散点图"""
    print("生成MNE对比散点图...")
    
    # 创建结果目录
    ensure_dir(Config.RESULTS_DIR)
    
    # 导入所需的图表生成代码
    try:
        sys.path.append("./eeg-web/test")
        from test_1_mne_comparison import create_comparison_chart
        
        # 调用图表生成函数
        create_comparison_chart(data)
        print(f"MNE对比散点图已保存到: {Config.RESULTS_DIR}/图5.2_MNE相关性散点图.png")
    except Exception as e:
        print(f"生成MNE对比散点图失败: {e}")
        
        # 如果导入失败，使用简化版本生成图表
        plt.figure(figsize=(10, 8), dpi=100)
        
        for band in data["eeg_web_results"].keys():
            plt.scatter(data["mne_results"][band], data["eeg_web_results"][band], label=band)
        
        plt.title("EEG-Web与MNE-Python分析结果对比")
        plt.xlabel("MNE-Python结果")
        plt.ylabel("EEG-Web结果")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 添加对角线
        min_val = min(plt.xlim()[0], plt.ylim()[0])
        max_val = max(plt.xlim()[1], plt.ylim()[1])
        plt.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5)
        
        plt.tight_layout()
        plt.savefig(f"{Config.RESULTS_DIR}/图5.2_MNE相关性散点图.png", dpi=300)
        plt.close()

def collect_preprocessing_performance(api_client):
    """收集预处理性能数据"""
    print("收集预处理性能数据...")
    data = api_client.get("/api/system/preprocess/performance")
    
    if data:
        # 保存数据
        ensure_dir(Config.DATA_DIR)
        with open(f"{Config.DATA_DIR}/preprocessing_performance.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 生成可视化
        generate_preprocessing_chart(data)
        return True
    else:
        print("无法获取预处理性能数据，请检查API是否可用")
        return False

def generate_preprocessing_chart(data):
    """生成预处理性能柱状图"""
    print("生成预处理性能柱状图...")
    
    # 创建结果目录
    ensure_dir(Config.RESULTS_DIR)
    
    # 导入所需的图表生成代码
    try:
        sys.path.append("./eeg-web/test")
        from test_2_preprocessing_performance import create_performance_chart
        
        # 调用图表生成函数
        create_performance_chart(data)
        print(f"预处理性能柱状图已保存到: {Config.RESULTS_DIR}/图5.3_预处理性能对比.png")
    except Exception as e:
        print(f"生成预处理性能柱状图失败: {e}")
        
        # 如果导入失败，使用简化版本生成图表
        plt.figure(figsize=(12, 8), dpi=100)
        
        methods = data["methods"]
        eeg_web_time = data["eeg_web_time"]
        mne_time = data["mne_time"]
        
        x = np.arange(len(methods))
        width = 0.35
        
        plt.bar(x - width/2, eeg_web_time, width, label='EEG-Web')
        plt.bar(x + width/2, mne_time, width, label='MNE-Python')
        
        plt.title("EEG-Web与MNE-Python预处理性能对比")
        plt.xlabel("预处理方法")
        plt.ylabel("处理时间(秒)")
        plt.xticks(x, methods)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(f"{Config.RESULTS_DIR}/图5.3_预处理性能对比.png", dpi=300)
        plt.close()

def collect_multimodal_analysis(api_client):
    """收集多模态分析数据"""
    print("收集多模态分析数据...")
    data = api_client.get("/api/system/analysis/multimodal")
    
    if data:
        # 保存数据
        ensure_dir(Config.DATA_DIR)
        with open(f"{Config.DATA_DIR}/multimodal_analysis.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 生成可视化
        generate_multimodal_chart(data)
        return True
    else:
        print("无法获取多模态分析数据，请检查API是否可用")
        return False

def generate_multimodal_chart(data):
    """生成多模态分析可视化示例图"""
    print("生成多模态分析可视化示例图...")
    
    # 创建结果目录
    ensure_dir(Config.RESULTS_DIR)
    
    # 导入所需的图表生成代码
    try:
        sys.path.append("./eeg-web/test")
        from test_3_multimodal_analysis import create_multimodal_visualization
        
        # 调用图表生成函数
        create_multimodal_visualization(data)
        print(f"多模态分析可视化示例图已保存到: {Config.RESULTS_DIR}/图5.5_多模态分析.png")
    except Exception as e:
        print(f"生成多模态分析可视化示例图失败: {e}")
        
        # 如果导入失败，使用简化版本生成图表
        plt.figure(figsize=(12, 10), dpi=100)
        
        # 绘制时域数据
        plt.subplot(2, 2, 1)
        for channel, signal in data["time_domain"]["signals"].items():
            plt.plot(data["time_domain"]["times"], signal, label=channel)
        plt.title("ERP波形")
        plt.xlabel("时间(s)")
        plt.ylabel("振幅(μV)")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 绘制频域数据
        plt.subplot(2, 2, 2)
        for channel, power in data["frequency_domain"]["powers"].items():
            plt.plot(data["frequency_domain"]["frequencies"], power, label=channel)
        plt.title("功率谱")
        plt.xlabel("频率(Hz)")
        plt.ylabel("功率(dB)")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(f"{Config.RESULTS_DIR}/图5.5_多模态分析.png", dpi=300)
        plt.close()

def collect_hardware_performance(api_client):
    """收集硬件性能数据"""
    print("收集硬件性能数据...")
    data = api_client.get("/api/system/hardware-performance")
    
    if data:
        # 保存数据
        ensure_dir(Config.DATA_DIR)
        with open(f"{Config.DATA_DIR}/hardware_performance.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 生成可视化
        generate_hardware_chart(data)
        return True
    else:
        print("无法获取硬件性能数据，请检查API是否可用")
        return False

def generate_hardware_chart(data):
    """生成硬件性能箱线图"""
    print("生成硬件性能箱线图...")
    
    # 创建结果目录
    ensure_dir(Config.RESULTS_DIR)
    
    # 导入所需的图表生成代码
    try:
        sys.path.append("./eeg-web/test")
        from test_4_hardware_performance import create_boxplot
        
        # 调用图表生成函数
        create_boxplot(data)
        print(f"硬件性能箱线图已保存到: {Config.RESULTS_DIR}/图5.6_交互帧率箱线图.png")
    except Exception as e:
        print(f"生成硬件性能箱线图失败: {e}")
        
        # 如果导入失败，使用简化版本生成图表
        plt.figure(figsize=(10, 8), dpi=100)
        
        # 创建箱线图
        sns.set_style("whitegrid")
        sns.boxplot(data=[data["fps_data"][config] for config in data["configs"]])
        
        plt.title("不同硬件配置下的交互帧率")
        plt.xlabel("硬件配置")
        plt.ylabel("帧率(FPS)")
        plt.xticks(range(len(data["configs"])), data["configs"])
        
        # 添加阈值线
        plt.axhline(y=30, color='orange', linestyle='--', label='流畅交互阈值(30 FPS)')
        plt.axhline(y=60, color='green', linestyle='--', label='最佳体验阈值(60 FPS)')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(f"{Config.RESULTS_DIR}/图5.6_交互帧率箱线图.png", dpi=300)
        plt.close()

def collect_response_times(api_client):
    """收集系统响应时间数据"""
    print("收集系统响应时间数据...")
    data = api_client.get("/api/system/response-times")
    
    if data:
        # 保存数据
        ensure_dir(Config.DATA_DIR)
        with open(f"{Config.DATA_DIR}/response_time.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 生成可视化
        generate_response_time_chart(data)
        return True
    else:
        print("无法获取系统响应时间数据，请检查API是否可用")
        return False

def generate_response_time_chart(data):
    """生成系统响应时间热力图"""
    print("生成系统响应时间热力图...")
    
    # 创建结果目录
    ensure_dir(Config.RESULTS_DIR)
    
    # 导入所需的图表生成代码
    try:
        sys.path.append("./eeg-web/test")
        from test_5_response_time import create_heatmap
        
        # 调用图表生成函数
        create_heatmap(data)
        print(f"系统响应时间热力图已保存到: {Config.RESULTS_DIR}/图5.7_响应时间热力图.png")
    except Exception as e:
        print(f"生成系统响应时间热力图失败: {e}")
        
        # 如果导入失败，使用简化版本生成图表
        plt.figure(figsize=(12, 10), dpi=100)
        
        operations = data["operations"]
        configs = data["configs"]
        response_data = np.array(data["data"])
        
        # 创建热力图
        sns.set_style("whitegrid")
        ax = sns.heatmap(response_data, annot=True, fmt=".2f", cmap="YlGnBu_r",
                     xticklabels=configs, yticklabels=operations)
        
        plt.title("系统响应时间分布(秒)")
        plt.xlabel("硬件配置")
        plt.ylabel("操作")
        
        plt.tight_layout()
        plt.savefig(f"{Config.RESULTS_DIR}/图5.7_响应时间热力图.png", dpi=300)
        plt.close()

def collect_concurrency_data(api_client):
    """收集并发性能数据"""
    print("收集并发性能数据...")
    data = api_client.get("/api/system/concurrency")
    
    if data:
        # 保存数据
        ensure_dir(Config.DATA_DIR)
        with open(f"{Config.DATA_DIR}/concurrency_test.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 生成可视化
        generate_concurrency_chart(data)
        return True
    else:
        print("无法获取并发性能数据，请检查API是否可用")
        return False

def generate_concurrency_chart(data):
    """生成并发性能曲面图"""
    print("生成并发性能曲面图...")
    
    # 创建结果目录
    ensure_dir(Config.RESULTS_DIR)
    
    # 导入所需的图表生成代码
    try:
        sys.path.append("./eeg-web/test")
        from test_6_concurrency import create_surface_plot
        
        # 调用图表生成函数
        create_surface_plot(data)
        print(f"并发性能曲面图已保存到: {Config.RESULTS_DIR}/图5.8_并发性能曲面.png")
    except Exception as e:
        print(f"生成并发性能曲面图失败: {e}")
        
        # 如果导入失败，使用简化版本生成图表
        plt.figure(figsize=(12, 8), dpi=100)
        
        concurrency = data["concurrency"]
        throughput = data["throughput"]
        response_time = data["response_time"]
        
        # 创建2D图表
        plt.subplot(1, 2, 1)
        plt.plot(concurrency, throughput, 'o-', color='blue')
        plt.title("并发用户数与吞吐量关系")
        plt.xlabel("并发用户数")
        plt.ylabel("吞吐量(请求/秒)")
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.subplot(1, 2, 2)
        plt.plot(concurrency, response_time, 'o-', color='red')
        plt.title("并发用户数与响应时间关系")
        plt.xlabel("并发用户数")
        plt.ylabel("响应时间(秒)")
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(f"{Config.RESULTS_DIR}/图5.8_并发性能曲面.png", dpi=300)
        plt.close()

def collect_resource_usage(api_client):
    """收集资源使用率数据"""
    print("收集资源使用率数据...")
    data = api_client.get("/api/system/resource-usage")
    
    if data:
        # 保存数据
        ensure_dir(Config.DATA_DIR)
        with open(f"{Config.DATA_DIR}/resource_usage.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 生成可视化
        generate_resource_usage_chart(data)
        return True
    else:
        print("无法获取资源使用率数据，请检查API是否可用")
        return False

def generate_resource_usage_chart(data):
    """生成资源使用率时序图"""
    print("生成资源使用率时序图...")
    
    # 创建结果目录
    ensure_dir(Config.RESULTS_DIR)
    
    # 导入所需的图表生成代码
    try:
        sys.path.append("./eeg-web/test")
        from test_7_resource_usage import create_resource_chart
        
        # 调用图表生成函数
        create_resource_chart(data)
        print(f"资源使用率时序图已保存到: {Config.RESULTS_DIR}/图5.9_资源利用率.png")
    except Exception as e:
        print(f"生成资源使用率时序图失败: {e}")
        
        # 如果导入失败，使用简化版本生成图表
        plt.figure(figsize=(12, 8), dpi=100)
        
        time_points = data["time_points"]
        cpu_usage = data["cpu_usage"]
        mem_usage = data["mem_usage"]
        
        plt.subplot(2, 1, 1)
        plt.plot(time_points, cpu_usage, 'b-', label='CPU使用率')
        plt.title("CPU使用率随时间变化")
        plt.xlabel("时间(分钟)")
        plt.ylabel("使用率(%)")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        plt.subplot(2, 1, 2)
        plt.plot(time_points, mem_usage, 'r-', label='内存使用率')
        plt.title("内存使用率随时间变化")
        plt.xlabel("时间(分钟)")
        plt.ylabel("使用率(%)")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(f"{Config.RESULTS_DIR}/图5.9_资源利用率.png", dpi=300)
        plt.close()

def main():
    """主函数"""
    print("=" * 60)
    print("EEG-Web系统性能数据收集与可视化脚本")
    print("=" * 60)
    
    # 确保结果目录存在
    ensure_dir(Config.RESULTS_DIR)
    ensure_dir(Config.DATA_DIR)
    
    # 创建API客户端
    api_client = APIClient()
    
    # 检查API是否可用
    print("检查API连接...")
    if not api_client.check_health():
        print("无法连接到EEG-Web API，请确保系统正在运行")
        print("API基础URL:", Config.API_BASE_URL)
        print("如果API地址不正确，请修改Config.API_BASE_URL")
        return
    
    print("API连接成功，开始收集数据...")
    
    # 收集各类数据并生成可视化
    results = []
    
    # 1. MNE对比数据
    results.append(collect_mne_comparison_data(api_client))
    
    # 2. 预处理性能数据
    results.append(collect_preprocessing_performance(api_client))
    
    # 3. 多模态分析数据
    results.append(collect_multimodal_analysis(api_client))
    
    # 4. 硬件性能数据
    results.append(collect_hardware_performance(api_client))
    
    # 5. 系统响应时间数据
    results.append(collect_response_times(api_client))
    
    # 6. 并发性能数据
    results.append(collect_concurrency_data(api_client))
    
    # 7. 资源使用率数据
    results.append(collect_resource_usage(api_client))
    
    # 输出结果摘要
    print("\n" + "=" * 60)
    print("数据收集与可视化结果摘要")
    print("=" * 60)
    
    success_count = sum(results)
    print(f"总计任务: 7, 成功: {success_count}, 失败: {7 - success_count}")
    
    if success_count == 7:
        print("\n所有数据收集与可视化任务已成功完成！")
        print(f"结果保存在: {Config.RESULTS_DIR}")
    else:
        print("\n部分任务失败，请检查上述错误信息")
    
    print("\n完成时间:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main() 