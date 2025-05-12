#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EEG-Web系统性能API测试脚本

此脚本用于测试EEG-Web系统性能API端点是否正常工作。
"""

import requests
import json
import os
from pathlib import Path

# API基础URL
API_BASE_URL = "http://localhost:8000"

# 测试目录
TEST_DIR = Path("./eeg-web/test")
DATA_DIR = TEST_DIR / "data"

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

def check_endpoint(endpoint, name):
    """检查API端点是否正常工作"""
    print(f"测试端点: {name} ({endpoint})")
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 检查响应格式
        if "data" in data:
            print(f"✓ {name}端点正常工作")
            
            # 保存响应数据
            filename = DATA_DIR / f"{name.lower().replace(' ', '_')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  数据已保存到: {filename}")
            
            return True
        else:
            print(f"✗ {name}端点响应格式不正确")
            return False
    except Exception as e:
        print(f"✗ {name}端点测试失败: {e}")
        return False

def test_all_endpoints():
    """测试所有系统性能API端点"""
    print("=" * 60)
    print("EEG-Web系统性能API测试")
    print("=" * 60)
    
    # 先检查健康状态
    health_ok = check_endpoint("/health", "健康检查")
    if not health_ok:
        print("API服务器未响应，请确保EEG-Web系统正在运行。")
        return
    
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
        result = check_endpoint(endpoint, name)
        results.append(result)
    
    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    
    success_count = sum(results)
    print(f"总计端点: {len(endpoints)}, 成功: {success_count}, 失败: {len(endpoints) - success_count}")
    
    if success_count == len(endpoints):
        print("\n所有端点测试通过！")
        print(f"数据保存在: {DATA_DIR}")
    else:
        print("\n部分端点测试失败，请检查上述错误信息")

if __name__ == "__main__":
    test_all_endpoints() 