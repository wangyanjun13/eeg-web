from fastapi import APIRouter, HTTPException
from app.models.data_analysis import ERPParams, TimeFreqParams
from app.models.common import APIResponse
from app.services.analysis_service import AnalysisService
from app.services.dataset_service import DatasetService
from pathlib import Path
from app.core.config import DATA_DIR
import math
import random

# 创建服务实例
# DATA_DIR = Path("/app/data/eeg_samples")
dataset_service = DatasetService(DATA_DIR)
analysis_service = AnalysisService(dataset_service)

router = APIRouter(prefix="/api/analysis")

# 注意：示例数据相关的端点已被移除，因为它们不再被前端使用
# 这些端点包括:
# - GET /api/analysis/examples/time
# - GET /api/analysis/examples/frequency
# - GET /api/analysis/examples/spatial
# - GET /api/analysis/examples/advanced

@router.get("/{dataset_id}/basic", response_model=APIResponse)
async def get_basic_info(dataset_id: str):
    """获取基本分析信息"""
    try:
        info = analysis_service.get_basic_info(dataset_id)
        return APIResponse(
            message="获取基本信息成功",
            data=info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/subjects/{subject_id}/erp", response_model=APIResponse)
async def compute_erp(dataset_id: str, subject_id: str, params: ERPParams):
    """计算ERP分析"""
    try:
        result = analysis_service.compute_erp(dataset_id, subject_id, params)
        return APIResponse(
            message="ERP分析完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/subjects/{subject_id}/time_freq", response_model=APIResponse)
async def compute_time_frequency(dataset_id: str, subject_id: str, params: TimeFreqParams):
    """计算时频分析"""
    try:
        result = analysis_service.compute_time_freq(dataset_id, subject_id, params)
        return APIResponse(
            message="时频分析完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/examples/time", response_model=APIResponse)
async def get_time_analysis_example():
    """获取时域分析示例数据"""
    try:
        # 生成示例数据
        example_data = {
            "erp": [
                {"channel": "Fz", "time": -0.2, "value": 0},
                {"channel": "Fz", "time": -0.1, "value": 1},
                {"channel": "Fz", "time": 0, "value": 2},
                {"channel": "Fz", "time": 0.1, "value": 3},
                {"channel": "Fz", "time": 0.2, "value": 2},
                {"channel": "Fz", "time": 0.3, "value": 1},
                {"channel": "Fz", "time": 0.4, "value": 0},
                {"channel": "Cz", "time": -0.2, "value": 0},
                {"channel": "Cz", "time": -0.1, "value": 0.5},
                {"channel": "Cz", "time": 0, "value": 1},
                {"channel": "Cz", "time": 0.1, "value": 1.5},
                {"channel": "Cz", "time": 0.2, "value": 1},
                {"channel": "Cz", "time": 0.3, "value": 0.5},
                {"channel": "Cz", "time": 0.4, "value": 0},
                {"channel": "Pz", "time": -0.2, "value": 0},
                {"channel": "Pz", "time": -0.1, "value": -0.5},
                {"channel": "Pz", "time": 0, "value": -1},
                {"channel": "Pz", "time": 0.1, "value": -1.5},
                {"channel": "Pz", "time": 0.2, "value": -1},
                {"channel": "Pz", "time": 0.3, "value": -0.5},
                {"channel": "Pz", "time": 0.4, "value": 0},
            ],
            "singleTrials": [
                {"channel": "Fz", "time": -0.2, "value": 0},
                {"channel": "Fz", "time": -0.1, "value": 1},
                {"channel": "Fz", "time": 0, "value": 2},
                {"channel": "Fz", "time": 0.1, "value": 3},
                {"channel": "Fz", "time": 0.2, "value": 2},
                {"channel": "Fz", "time": 0.3, "value": 1},
                {"channel": "Fz", "time": 0.4, "value": 0},
            ],
            "timeSeries": [
                {"channel": "Fz", "time": 0, "value": 0},
                {"channel": "Fz", "time": 1, "value": 1},
                {"channel": "Fz", "time": 2, "value": 2},
                {"channel": "Fz", "time": 3, "value": 1},
                {"channel": "Fz", "time": 4, "value": 0},
                {"channel": "Fz", "time": 5, "value": -1},
                {"channel": "Fz", "time": 6, "value": -2},
                {"channel": "Fz", "time": 7, "value": -1},
                {"channel": "Fz", "time": 8, "value": 0},
                {"channel": "Fz", "time": 9, "value": 1},
                {"channel": "Fz", "time": 10, "value": 0},
            ]
        }
        return {"code": 200, "message": "获取示例数据成功", "data": example_data}
    except Exception as e:
        logger.error(f"获取时域分析示例数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取时域分析示例数据失败: {str(e)}")

@router.get("/examples/frequency", response_model=APIResponse)
async def get_frequency_analysis_example():
    """获取频域分析示例数据"""
    try:
        # 生成示例数据
        frequencies = [i for i in range(0, 51)]
        channels = ["Fz", "Cz", "Pz"]
        
        # 生成不同通道的功率谱
        powers = {}
        for ch in channels:
            if ch == "Fz":
                # Fz通道有明显的Alpha峰
                powers[ch] = [0.1 * i if i < 8 else (5 if 8 <= i <= 12 else (0.1 * (50 - i))) for i in frequencies]
            elif ch == "Cz":
                # Cz通道有明显的Beta峰
                powers[ch] = [0.1 * i if i < 13 else (3 if 13 <= i <= 30 else (0.1 * (50 - i))) for i in frequencies]
            else:
                # Pz通道有明显的Theta峰
                powers[ch] = [0.1 * i if i < 4 else (4 if 4 <= i <= 7 else (0.1 * (50 - i))) for i in frequencies]
        
        # 生成时频数据
        time_points = [i/10 for i in range(-20, 81)]  # -200ms到800ms
        time_freq_data = []
        
        for ch in channels:
            for t_idx, t in enumerate(time_points):
                for f_idx, f in enumerate(frequencies):
                    if f <= 40:  # 只显示到40Hz
                        # 生成随机值，但保持一定的结构
                        if ch == "Fz" and 8 <= f <= 12 and t >= 0.1:
                            value = 3 + 2 * math.sin(t) + random.random()
                        elif ch == "Cz" and 13 <= f <= 30 and t >= 0.2:
                            value = 2 + math.sin(t) + random.random()
                        elif ch == "Pz" and 4 <= f <= 7 and t >= 0:
                            value = 4 + 3 * math.sin(t) + random.random()
                        else:
                            value = random.random()
                        
                        time_freq_data.append({
                            "channel": ch,
                            "time": t,
                            "frequency": f,
                            "power": value
                        })
        
        example_data = {
            "spectrum": {
                "frequencies": frequencies,
                "channels": channels,
                "powers": powers
            },
            "timeFrequency": time_freq_data
        }
        
        return {"code": 200, "message": "获取示例数据成功", "data": example_data}
    except Exception as e:
        logger.error(f"获取频域分析示例数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取频域分析示例数据失败: {str(e)}")

@router.get("/examples/spatial", response_model=APIResponse)
async def get_spatial_analysis_example():
    """获取空间分析示例数据"""
    try:
        # 生成示例数据 - 简单的头皮地形图数据
        # 标准10-20系统电极位置
        positions = {
            "Fp1": [-0.3, -0.4], "Fp2": [0.3, -0.4],
            "F7": [-0.5, -0.2], "F3": [-0.3, -0.2], "Fz": [0, -0.2], "F4": [0.3, -0.2], "F8": [0.5, -0.2],
            "T3": [-0.5, 0], "C3": [-0.3, 0], "Cz": [0, 0], "C4": [0.3, 0], "T4": [0.5, 0],
            "T5": [-0.5, 0.2], "P3": [-0.3, 0.2], "Pz": [0, 0.2], "P4": [0.3, 0.2], "T6": [0.5, 0.2],
            "O1": [-0.3, 0.4], "O2": [0.3, 0.4]
        }
        
        # 生成示例值 - Alpha波在后部更强
        channels = list(positions.keys())
        values = []
        
        for ch in channels:
            # 前部电极值较小，后部电极值较大
            if "F" in ch or "Fp" in ch:
                values.append(random.uniform(0.5, 2.0))
            elif "C" in ch or "T" in ch:
                values.append(random.uniform(2.0, 4.0))
            elif "P" in ch or "O" in ch:
                values.append(random.uniform(4.0, 6.0))
        
        # 添加多个时间点
        time_points = [0, 100, 200, 300, 400, 500]
        
        example_data = {
            "positions": list(positions.values()),
            "channels": channels,
            "values": values,
            "timePoints": time_points
        }
        
        return {"code": 200, "message": "获取示例数据成功", "data": example_data}
    except Exception as e:
        logger.error(f"获取空间分析示例数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取空间分析示例数据失败: {str(e)}") 