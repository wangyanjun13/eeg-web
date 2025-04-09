from fastapi import APIRouter, HTTPException
from app.models.data_preprocess import FilterParams, ICAParams, ArtifactParams, PreprocessParams
from app.models.common import APIResponse
from app.services.preprocess_service import PreprocessService
from app.services.dataset_service import DatasetService
from pathlib import Path

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
            
        result = preprocess_service.apply_filter(dataset_id, subject_id, params)
        
        # 检查结果是否有效
        if not result or not hasattr(result, 'data') or not result.data:
            raise ValueError("滤波处理返回了无效的数据")
            
        return APIResponse(
            success=True,
            message="滤波处理完成",
            data=result
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