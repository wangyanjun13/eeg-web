from fastapi import APIRouter, HTTPException
from app.models.data_preprocess import FilterParams, ICAParams, ArtifactParams, PreprocessParams, SegmentParams, BadSegmentParams, ResampleParams
from app.models.common import APIResponse
from app.services.preprocess_service import PreprocessService
from app.services.dataset_service import DatasetService
from pathlib import Path
import time
from fastapi.responses import Response

# 导入缓存相关函数
from app.core.config import get_preprocess_cache_key
from app.core.redis import get_metadata, save_metadata, get_from_cache, save_to_cache

# 创建服务实例
DATA_DIR = Path("/app/data/eeg_samples")
dataset_service = DatasetService(DATA_DIR)
preprocess_service = PreprocessService(dataset_service)

router = APIRouter(prefix="/api/preprocess")

@router.get("/templates/{template_name}", response_model=APIResponse)
async def get_preprocess_template(template_name: str):
    """获取预处理模板
    
    Args:
        template_name: 模板名称
    """
    try:
        template = PreprocessParams.get_template(template_name)
        return APIResponse(
            message=f"获取{template_name}模板成功",
            data=template
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates", response_model=APIResponse)
async def get_all_templates():
    """获取所有预处理模板"""
    try:
        templates = {
            "default": PreprocessParams.get_template("default"),
            "minimal": PreprocessParams.get_template("minimal"),
            "ds002218": PreprocessParams.get_template("ds002218")
        }
        return APIResponse(
            message="获取所有模板成功",
            data=templates
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/{subject_id}", response_model=APIResponse)
async def preprocess_data(dataset_id: str, subject_id: str, params: PreprocessParams):
    """执行完整预处理流程"""
    try:
        # 实际应用所有预处理步骤，而不只是滤波
        # 滤波、重采样、重参考、ICA、坏通道检测、去伪迹
        result = preprocess_service.apply_complete_preprocessing(dataset_id, subject_id, params)
        return APIResponse(
            message="预处理完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/subjects/{subject_id}/filter", response_model=APIResponse)
async def apply_filter(dataset_id: str, subject_id: str, params: FilterParams):
    """应用滤波器
    
    Args:
        dataset_id: 数据集ID
        subject_id: 受试者ID
        params: 滤波参数
            - highpass_filter: 是否启用高通滤波
            - highpass: 高通截止频率
            - lowpass_filter: 是否启用低通滤波
            - lowpass: 低通截止频率
            - notch_filter: 是否启用陷波滤波
            - line_freqs: 陷波频率列表
    """
    try:
        # 输出接收到的参数，帮助调试
        print(f"接收到滤波请求: dataset_id={dataset_id}, subject_id={subject_id}")
        print(f"滤波参数: {params.dict()}")
        
        # 参数验证
        if params.highpass_filter and params.highpass <= 0:
            raise ValueError("高通滤波频率必须大于0")
        if params.lowpass_filter and params.lowpass <= 0:
            raise ValueError("低通滤波频率必须大于0")
        if params.notch_filter and not params.line_freqs:
            raise ValueError("启用陷波滤波时必须指定频率")
            
        # 处理通道参数
        channels = params.dict().pop("channels", None) if hasattr(params, "channels") else None
            
        # 记录处理开始时间
        start_time = time.time()
        
        # 检查缓存
        cache_key = get_preprocess_cache_key(dataset_id, subject_id, "filter")
        cache_meta_key = f"{cache_key}:meta"
        
        from_cache = False
        process_time = 0
        
        # 检查元数据
        cached_meta = get_metadata(cache_meta_key)
        if cached_meta:
            # 检查参数是否匹配
            params_dict = params.dict()
            if channels:
                params_dict['channels'] = channels
                
            # 参数一致则标记为从缓存获取
            if cached_meta.get('params') == params_dict:
                from_cache = True
                process_time = cached_meta.get('process_time', 0)
        
        # 执行处理
        result = preprocess_service.apply_filter(dataset_id, subject_id, params, channels)
        
        # 如果不是从缓存获取，计算处理时间
        if not from_cache:
            process_time = time.time() - start_time
        
        # 创建响应
        response = APIResponse(
            success=True,
            message="滤波处理完成",
            data=result
        )
        
        # 返回响应，添加自定义头信息
        return Response(
            content=response.json(),
            media_type="application/json",
            headers={
                "X-From-Cache": str(from_cache).lower(),
                "X-Process-Time": str(process_time)
            }
        )
    except ValueError as e:
        error_msg = f"参数错误: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"滤波处理失败: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/{dataset_id}/subjects/{subject_id}/ica", response_model=APIResponse)
async def run_ica(dataset_id: str, subject_id: str, params: ICAParams):
    """运行ICA分析
    
    Args:
        dataset_id: 数据集ID
        subject_id: 受试者ID
        params: ICA参数
            - n_components: ICA组件数量
            - random_state: 随机数种子
    """
    try:
        result = preprocess_service.run_ica(dataset_id, subject_id, params)
        return APIResponse(
            message="ICA分析完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/subjects/{subject_id}/artifacts", response_model=APIResponse)
async def remove_artifacts(dataset_id: str, subject_id: str, params: ArtifactParams):
    """去除伪迹
    
    Args:
        dataset_id: 数据集ID
        subject_id: 受试者ID
        params: 伪迹去除参数
            - eog: 是否去除眼电伪迹
            - ecg: 是否去除心电伪迹
            - threshold: 伪迹检测阈值
    """
    try:
        result = preprocess_service.remove_artifacts(dataset_id, subject_id, params)
        return APIResponse(
            message="伪迹去除完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/subjects/{subject_id}/status", response_model=APIResponse)
async def get_preprocess_status(dataset_id: str, subject_id: str):
    """获取预处理状态
    
    Args:
        dataset_id: 数据集ID
        subject_id: 受试者ID
    """
    try:
        return APIResponse(
            message="获取预处理状态成功",
            data={
                "dataset_id": dataset_id,
                "subject_id": subject_id,
                "applied_methods": [],  # 已应用的预处理方法
                "available_methods": [  # 可用的预处理方法
                    "filter",
                    "ica",
                    "artifacts"
                ]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/subjects/{subject_id}/segment", response_model=APIResponse)
async def segment_data(dataset_id: str, subject_id: str, params: SegmentParams):
    """数据分段
    
    Args:
        dataset_id: 数据集ID
        subject_id: 受试者ID
        params: 分段参数
    """
    try:
        result = preprocess_service.segment_data(dataset_id, subject_id, params)
        return APIResponse(
            message="数据分段完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/subjects/{subject_id}/bad_segments", response_model=APIResponse)
async def detect_bad_segments(dataset_id: str, subject_id: str, params: BadSegmentParams):
    """检测并剔除坏段
    
    Args:
        dataset_id: 数据集ID
        subject_id: 受试者ID
        params: 坏段检测与剔除参数
    """
    try:
        result = preprocess_service.detect_bad_segments(dataset_id, subject_id, params)
        return APIResponse(
            message="坏段处理完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/subjects/{subject_id}/resample", response_model=APIResponse)
async def apply_resample(dataset_id: str, subject_id: str, params: ResampleParams):
    """应用重采样
    
    Args:
        dataset_id: 数据集ID
        subject_id: 受试者ID
        params: 重采样参数
            - resample: 是否开启重采样
            - resample_freq: 目标采样频率
    """
    try:
        # 输出接收到的参数，帮助调试
        print(f"接收到重采样请求: dataset_id={dataset_id}, subject_id={subject_id}")
        print(f"重采样参数: {params.dict()}")
        
        # 参数验证
        if params.resample and params.resample_freq <= 0:
            raise ValueError("重采样频率必须大于0Hz")
            
        # 处理通道参数
        channels = params.dict().pop("channels", None) if hasattr(params, "channels") else None
            
        # 记录处理开始时间
        start_time = time.time()
        
        # 检查缓存
        cache_key = get_preprocess_cache_key(dataset_id, subject_id, "resample")
        cache_meta_key = f"{cache_key}:meta"
        
        from_cache = False
        process_time = 0
        
        # 检查元数据
        cached_meta = get_metadata(cache_meta_key)
        if cached_meta:
            # 检查参数是否匹配
            params_dict = params.dict()
            if channels:
                params_dict['channels'] = channels
                
            # 参数一致则标记为从缓存获取
            if cached_meta.get('params') == params_dict:
                from_cache = True
                process_time = cached_meta.get('process_time', 0)
        
        # 执行处理
        result = preprocess_service.apply_resample(dataset_id, subject_id, params, channels)
        
        # 如果不是从缓存获取，计算处理时间
        if not from_cache:
            process_time = time.time() - start_time
        
        # 创建响应
        response = APIResponse(
            success=True,
            message="重采样处理完成",
            data=result
        )
        
        # 返回响应，添加自定义头信息
        return Response(
            content=response.json(),
            media_type="application/json",
            headers={
                "X-From-Cache": str(from_cache).lower(),
                "X-Process-Time": str(process_time)
            }
        )
    except ValueError as e:
        error_msg = f"参数错误: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"重采样处理失败: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/{dataset_id}/subjects/{subject_id}/events", response_model=APIResponse)
async def get_events(dataset_id: str, subject_id: str):
    """获取数据集中事件信息
    
    Args:
        dataset_id: 数据集ID
        subject_id: 受试者ID
    """
    try:
        events = dataset_service.get_events_info(dataset_id, subject_id)
        return APIResponse(
            message="获取事件信息成功",
            data=events
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
    
