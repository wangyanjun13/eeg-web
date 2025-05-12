"""
EEG-Web系统性能数据API路由示例

将这些路由添加到您的FastAPI后端，以便run_all_tests.py可以收集实际系统数据。
"""

import sys
import os
from pathlib import Path

# 将backend目录添加到Python路径
backend_path = str(Path(__file__).parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

from fastapi import APIRouter, HTTPException
import json
import time
import numpy as np
import psutil
from typing import Dict, List, Any

# 创建路由器
router = APIRouter(prefix="/api/system", tags=["system"])

# 健康检查端点 - 复用现有端点
@router.get("/health")
def health_check():
    """系统健康检查"""
    # 这里不需要实现，主应用中已经有health端点

# MNE对比数据端点
@router.get("/mne-comparison")
def get_mne_comparison():
    """
    返回系统与MNE-Python的分析结果对比数据
    这应该从您的系统中实际收集数据
    """
    try:
        # 示例：从您系统的数据库或缓存中获取实际数据
        # 这里仅作示例，您需要替换为实际的数据收集逻辑
        
        # 假设您有一个函数来获取最近的MNE对比结果
        # results = your_system.get_recent_mne_comparison_results()
        
        # 示例数据结构
        subjects = [f"S{i:03d}" for i in range(1, 11)]
        
        # 这里应该是您系统中实际的分析结果
        eeg_web_results = {
            "alpha": [23.5, 24.7, 22.1, 21.9, 25.3, 24.1, 22.8, 23.7, 24.9, 23.2],
            "beta": [12.3, 11.9, 13.5, 12.7, 11.8, 12.5, 13.1, 12.8, 11.7, 12.4],
            "theta": [8.2, 7.9, 8.5, 8.1, 7.8, 8.3, 7.7, 8.4, 8.0, 7.9],
            "delta": [4.5, 4.2, 4.7, 4.3, 4.1, 4.6, 4.4, 4.8, 4.5, 4.3],
            "gamma": [3.2, 3.5, 3.1, 3.4, 3.3, 3.0, 3.6, 3.2, 3.4, 3.1]
        }
        
        # 这里应该是MNE-Python的对应分析结果
        mne_results = {
            "alpha": [24.1, 25.2, 22.5, 22.3, 25.8, 24.5, 23.2, 24.1, 25.3, 23.6],
            "beta": [12.5, 12.1, 13.7, 12.9, 12.0, 12.7, 13.3, 13.0, 11.9, 12.6],
            "theta": [8.3, 8.0, 8.7, 8.2, 7.9, 8.5, 7.8, 8.6, 8.1, 8.0],
            "delta": [4.6, 4.3, 4.8, 4.4, 4.2, 4.7, 4.5, 4.9, 4.6, 4.4],
            "gamma": [3.3, 3.6, 3.2, 3.5, 3.4, 3.1, 3.7, 3.3, 3.5, 3.2]
        }
        
        data = {
            "subjects": subjects,
            "eeg_web_results": eeg_web_results,
            "mne_results": mne_results
        }
        
        return APIResponse(
            message="获取MNE对比数据成功",
            data=data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取MNE对比数据失败: {str(e)}")

# 预处理性能数据端点
@router.get("/preprocess/performance")
def get_preprocessing_performance():
    """
    返回系统预处理性能数据，与MNE-Python对比
    这应该从您的系统中实际收集数据
    """
    try:
        # 示例：从您系统的性能监控中获取实际数据
        # 这里仅作示例，您需要替换为实际的数据收集逻辑
        
        # 假设您有一个函数来获取预处理性能数据
        # results = your_system.get_preprocessing_performance_metrics()
        
        # 示例数据结构
        methods = ["滤波", "重采样", "去伪迹", "重参考", "ICA分析"]
        
        # 这里应该是您系统中实际的处理时间
        eeg_web_time = [1.5, 1.2, 2.8, 1.0, 5.2]
        
        # 这里应该是MNE-Python的对应处理时间
        mne_time = [2.3, 1.8, 4.2, 1.5, 8.7]
        
        data = {
            "methods": methods,
            "eeg_web_time": eeg_web_time,
            "mne_time": mne_time
        }
        
        return APIResponse(
            message="获取预处理性能数据成功",
            data=data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预处理性能数据失败: {str(e)}")

# 多模态分析数据端点
@router.get("/analysis/multimodal")
def get_multimodal_analysis():
    """
    返回系统多模态分析数据
    这应该从您的系统中实际收集数据
    """
    try:
        # 示例：从您系统的分析结果中获取实际数据
        # 这里仅作示例，您需要替换为实际的数据收集逻辑
        
        # 假设您有一个函数来获取多模态分析数据
        # results = your_system.get_multimodal_analysis_results()
        
        # 示例数据结构 - 这里应该是您系统中实际的分析结果
        time_domain = {
            "times": np.linspace(-0.2, 0.8, 200).tolist(),
            "signals": {
                "Fz": (2*np.exp(-(np.linspace(-0.2, 0.8, 200)-0.3)**2/0.02) - 
                       0.8*np.exp(-(np.linspace(-0.2, 0.8, 200)-0.15)**2/0.01) + 
                       0.2*np.random.randn(200)).tolist(),
                "Cz": (3*np.exp(-(np.linspace(-0.2, 0.8, 200)-0.35)**2/0.015) - 
                       0.5*np.exp(-(np.linspace(-0.2, 0.8, 200)-0.1)**2/0.01) + 
                       0.2*np.random.randn(200)).tolist(),
                "Pz": (3.5*np.exp(-(np.linspace(-0.2, 0.8, 200)-0.3)**2/0.01) - 
                       0.3*np.exp(-(np.linspace(-0.2, 0.8, 200)-0.2)**2/0.02) + 
                       0.2*np.random.randn(200)).tolist()
            }
        }
        
        frequency_domain = {
            "frequencies": np.linspace(0, 50, 100).tolist(),
            "powers": {
                "Fz": (5*np.exp(-(np.linspace(0, 50, 100)-6)**2/8) + 
                       3*np.exp(-(np.linspace(0, 50, 100)-10)**2/4) + 
                       1.5*np.exp(-(np.linspace(0, 50, 100)-20)**2/30) + 0.1).tolist(),
                "Cz": (3*np.exp(-(np.linspace(0, 50, 100)-6)**2/10) + 
                       6*np.exp(-(np.linspace(0, 50, 100)-10)**2/5) + 
                       2*np.exp(-(np.linspace(0, 50, 100)-20)**2/20) + 0.1).tolist(),
                "Pz": (2*np.exp(-(np.linspace(0, 50, 100)-5)**2/12) + 
                       8*np.exp(-(np.linspace(0, 50, 100)-10)**2/4) + 
                       1*np.exp(-(np.linspace(0, 50, 100)-22)**2/50) + 0.1).tolist()
            }
        }
        
        data = {
            "time_domain": time_domain,
            "frequency_domain": frequency_domain,
        }
        
        return APIResponse(
            message="获取多模态分析数据成功",
            data=data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取多模态分析数据失败: {str(e)}")

# 硬件性能数据端点
@router.get("/hardware-performance")
def get_hardware_performance():
    """
    返回不同硬件配置下的系统性能数据
    这应该从您的系统中实际收集数据
    """
    try:
        # 示例：从您系统的性能测试结果中获取实际数据
        # 这里仅作示例，您需要替换为实际的数据收集逻辑
        
        # 假设您有一个函数来获取硬件性能数据
        # results = your_system.get_hardware_performance_metrics()
        
        # 示例数据结构
        configs = ['低性能配置', '中性能配置', '高性能配置']
        
        # 这里应该是您系统中实际的性能数据
        np.random.seed(42)
        fps_data = {
            '低性能配置': np.clip(np.random.normal(17, 4, 20), 6, 28).tolist(),
            '中性能配置': np.clip(np.random.normal(32, 5, 20), 16, 45).tolist(),
            '高性能配置': np.clip(np.random.normal(57, 6, 20), 38, 75).tolist()
        }
        
        data = {
            "configs": configs,
            "fps_data": fps_data
        }
        
        return APIResponse(
            message="获取硬件性能数据成功",
            data=data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取硬件性能数据失败: {str(e)}")

# 系统响应时间数据端点
@router.get("/response-times")
def get_response_times():
    """
    返回系统在不同配置下的响应时间数据
    这应该从您的系统中实际收集数据
    """
    try:
        # 示例：从您系统的性能监控中获取实际数据
        # 这里仅作示例，您需要替换为实际的数据收集逻辑
        
        # 假设您有一个函数来获取响应时间数据
        # results = your_system.get_response_time_metrics()
        
        # 示例数据结构
        operations = ['数据加载', '基础滤波', 'ICA处理', '时频分析', 
                     '头皮地形图', '连通性分析', '3D可视化', '文件导出']
        configs = ['低配', '中配', '高配']
        
        # 这里应该是您系统中实际的响应时间数据
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
        data = (base_times + noise).tolist()
        
        return APIResponse(
            message="获取响应时间数据成功",
            data={
                "operations": operations,
                "configs": configs,
                "data": data
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取响应时间数据失败: {str(e)}")

# 并发性能数据端点
@router.get("/concurrency")
def get_concurrency_performance():
    """
    返回系统并发性能数据
    这应该从您的系统中实际收集数据
    """
    try:
        # 示例：从您系统的并发测试结果中获取实际数据
        # 这里仅作示例，您需要替换为实际的数据收集逻辑
        
        # 假设您有一个函数来获取并发性能数据
        # results = your_system.get_concurrency_performance_metrics()
        
        # 示例数据结构
        concurrency = np.arange(5, 81, 5).tolist()  # 5到80个并发用户
        
        # 这里应该是您系统中实际的并发性能数据
        throughput_base = np.zeros_like(concurrency, dtype=float)
        for i, c in enumerate(concurrency):
            if c <= 40:  # 40个并发前基本线性上升
                throughput_base[i] = 0.75 + 0.2 * (c / 40)
            else:  # 超过40个并发后性能开始下降
                throughput_base[i] = 0.95 - 0.3 * ((c - 40) / 40)
        
        # 添加随机波动
        np.random.seed(42)
        throughput = (throughput_base + np.random.uniform(-0.03, 0.03, size=len(concurrency))).tolist()
        
        # 响应时间随并发用户数增加而增加
        response_time_base = 0.05 + 0.02 * np.array(concurrency) + 0.0015 * np.array(concurrency)**2
        response_time = (response_time_base + np.random.uniform(-0.1, 0.1, size=len(concurrency))).tolist()
        
        data = {
            "concurrency": concurrency,
            "throughput": throughput,
            "response_time": response_time
        }
        
        return APIResponse(
            message="获取并发性能数据成功",
            data=data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取并发性能数据失败: {str(e)}")

# 资源使用数据端点
@router.get("/resource-usage")
def get_resource_usage():
    """
    返回系统资源使用数据
    这应该从您的系统中实际收集数据
    """
    try:
        # 示例：从您系统的资源监控中获取实际数据
        # 这里仅作示例，您需要替换为实际的数据收集逻辑
        
        # 假设您有一个函数来获取资源使用数据
        # results = your_system.get_resource_usage_metrics()
        
        # 示例数据结构
        time_points = np.arange(0, 120, 2).tolist()  # 0到118分钟，每2分钟一个采样点
        
        # 这里应该是您系统中实际的资源使用数据
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
        
        # 内存使用率
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
        
        return APIResponse(
            message="获取资源使用数据成功",
            data=data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资源使用数据失败: {str(e)}")

# 添加这些路由到您的FastAPI应用
# 在您的main.py中:
# from .api_routes_example import router as system_router
# app.include_router(system_router)

# 导入模块错误处理
try:
    from app.models.common import APIResponse
except ImportError:
    # 定义替代的APIResponse类
    class APIResponse(dict):
        def __init__(self, message="", data=None, status="success"):
            super().__init__(message=message, data=data or {}, status=status) 