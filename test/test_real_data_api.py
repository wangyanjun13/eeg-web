#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EEG-Web系统真实数据API测试脚本

此脚本测试系统性能API是否正确收集和返回实际数据。
"""

import os
import json
import time
import requests
from pathlib import Path
import matplotlib.pyplot as plt

# API基础URL
API_BASE_URL = "http://localhost:8000"

# 测试目录
TEST_DIR = Path("./eeg-web/test")
DATA_DIR = TEST_DIR / "testing_data"
RESULTS_DIR = Path("./testing_results")

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def check_data_source(data):
    """
    检查API返回的数据是否包含真实数据的指示
    """
    # 检查数据源字段
    data_source = None
    if "data_source" in data:
        data_source = data["data_source"]
        
    elif "data_sources" in data:
        data_source = data["data_sources"]
        
    if not data_source:
        if "successful_retrievals" in data and data["successful_retrievals"] > 0:
            return "部分真实数据"
        return "未知"
    
    # 检查字符串数据源
    if isinstance(data_source, str):
        if "实际" in data_source or "真实" in data_source or "real" in data_source:
            return "真实数据"
        elif "估算" in data_source or "模拟" in data_source or "simulated" in data_source:
            return "模拟数据"
        else:
            return f"混合数据 ({data_source})"
    
    # 检查字典或列表数据源
    if isinstance(data_source, dict) or isinstance(data_source, list):
        real_count = sum(1 for s in str(data_source) if "实际" in s or "真实" in s or "real" in s)
        sim_count = sum(1 for s in str(data_source) if "估算" in s or "模拟" in s or "simulated" in s)
        
        if real_count > 0 and sim_count > 0:
            return f"混合数据 (真实:{real_count}, 模拟:{sim_count})"
        elif real_count > 0:
            return "真实数据"
        elif sim_count > 0:
            return "模拟数据"
    
    return "未知"

def test_endpoint(endpoint, name):
    """测试API端点并检查数据来源"""
    print(f"\n测试端点: {name} ({endpoint})")
    try:
        # 多次访问以创建真实使用数据
        for _ in range(3):
            _ = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
            time.sleep(0.5)
        
        # 最后一次请求获取实际结果
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # 检查响应格式
        if "data" in result:
            data = result["data"]
            data_source = check_data_source(data)
            
            print(f"✓ {name}端点正常工作")
            print(f"  数据来源: {data_source}")
            
            # 保存响应数据
            filename = DATA_DIR / f"{name.lower().replace(' ', '_')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"  数据已保存到: {filename}")
            
            return True, data_source
        else:
            print(f"✗ {name}端点响应格式不正确")
            return False, "未知"
    except Exception as e:
        print(f"✗ {name}端点测试失败: {e}")
        return False, "错误"

def test_performance():
    """测试系统性能模拟和数据收集"""
    print("\n正在进行性能负载测试，模拟多个并发请求...")
    
    # 并发请求数
    concurrent_requests = 20
    endpoint = "/health"
    
    import concurrent.futures
    
    def make_request(_):
        try:
            start = time.time()
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
            duration = time.time() - start
            return response.status_code, duration
        except Exception as e:
            return 0, 0
    
    # 执行并发请求
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        results = list(executor.map(make_request, range(concurrent_requests)))
    
    success_count = sum(1 for status, _ in results if status == 200)
    avg_response_time = sum(duration for _, duration in results if duration > 0) / max(1, len([d for _, d in results if d > 0]))
    
    print(f"并发请求测试结果: 成功 {success_count}/{concurrent_requests}, 平均响应时间: {avg_response_time:.4f}秒")
    
    # 休息一会让系统记录数据
    time.sleep(2)

def create_data_source_chart(results):
    """创建数据来源图表"""
    endpoints = [r[0] for r in results]
    data_sources = [r[1] for r in results]
    
    # 数据源类型统计
    source_types = {}
    for source in data_sources:
        if source not in source_types:
            source_types[source] = 0
        source_types[source] += 1
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    
    # 端点数据来源柱状图
    plt.subplot(1, 2, 1)
    colors = []
    for source in data_sources:
        if "真实" in source:
            colors.append('green')
        elif "混合" in source:
            colors.append('orange')
        elif "模拟" in source:
            colors.append('red')
        else:
            colors.append('gray')
    
    plt.bar(endpoints, [1] * len(endpoints), color=colors)
    plt.xticks(rotation=45, ha='right')
    plt.title('API端点数据来源类型')
    plt.tight_layout()
    
    # 数据源占比饼图
    plt.subplot(1, 2, 2)
    source_labels = list(source_types.keys())
    source_counts = list(source_types.values())
    
    pie_colors = []
    for source in source_labels:
        if "真实" in source:
            pie_colors.append('green')
        elif "混合" in source:
            pie_colors.append('orange')
        elif "模拟" in source:
            pie_colors.append('red')
        else:
            pie_colors.append('gray')
    
    plt.pie(source_counts, labels=source_labels, colors=pie_colors, autopct='%1.1f%%')
    plt.title('数据来源分布')
    
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "系统性能数据来源分析.png", dpi=300)
    plt.close()
    
    print(f"\n数据来源分析图表已保存到: {RESULTS_DIR}/系统性能数据来源分析.png")

def main():
    """主测试函数"""
    print("=" * 60)
    print("EEG-Web系统真实数据API测试")
    print("=" * 60)
    print("本测试将检查API是否返回真实的系统性能数据")
    
    # 先检查健康状态
    health_ok, _ = test_endpoint("/health", "健康检查")
    if not health_ok:
        print("API服务器未响应，请确保EEG-Web系统正在运行。")
        return
    
    # 执行性能测试生成一些真实数据
    test_performance()
    
    # 测试所有性能数据端点
    endpoints = [
        ("/api/system/mne-comparison", "MNE对比数据"),
        ("/api/system/preprocess/performance", "预处理性能数据"),
        ("/api/system/analysis/multimodal", "多模态分析数据"),
        ("/api/system/hardware-performance", "硬件性能数据"),
        ("/api/system/response-times", "响应时间数据"),
        ("/api/system/concurrency", "并发性能数据"),
        ("/api/system/resource-usage", "资源使用率数据")
    ]
    
    results = []
    for endpoint, name in endpoints:
        success, data_source = test_endpoint(endpoint, name)
        if success:
            results.append((name, data_source))
    
    # 分析和展示结果
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    
    if results:
        # 统计各种数据源
        real_data_count = sum(1 for _, source in results if "真实" in source)
        mixed_data_count = sum(1 for _, source in results if "混合" in source)
        simulated_data_count = sum(1 for _, source in results if "模拟" in source or "估算" in source)
        
        print(f"总计端点: {len(results)}")
        print(f"使用真实数据的端点: {real_data_count}")
        print(f"使用混合数据的端点: {mixed_data_count}")
        print(f"使用模拟数据的端点: {simulated_data_count}")
        
        # 创建数据来源图表
        create_data_source_chart(results)
        
        if real_data_count + mixed_data_count > 0:
            print("\n✓ 系统已部分或完全使用真实数据")
            if simulated_data_count > 0:
                print("  一些端点仍在使用模拟数据，随着系统使用将逐渐收集更多真实数据")
        else:
            print("\n⚠ 系统当前仅使用模拟数据")
            print("  需要更多系统使用才能收集真实数据")
    else:
        print("没有成功测试的端点")

    print("\n要增加真实数据的比例，请:")
    print("1. 确保系统正常运行并处理实际EEG数据")
    print("2. 增加系统使用量，进行更多预处理和分析操作")
    print("3. 执行负载测试，生成并发性能数据")
    print("4. 检查日志目录是否已正确创建并有写入权限")

if __name__ == "__main__":
    main() 