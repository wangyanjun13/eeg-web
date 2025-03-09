from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mne
import os
from pathlib import Path
from .routes import analysis_router, visualization_router, participants_router
from .routes.analysis import init_eeg_service
import pandas as pd

app = FastAPI(
    title="EEG Analyzer",
    description="EEG数据分析平台",
    version="1.0.0",
    docs_url="/docs",   # 明确指定文档URL
    redoc_url="/redoc"  # 明确指定ReDoc URL
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取项目根目录的绝对路径
BASE_DIR = Path("/app")  # 在Docker容器中的路径
DATA_DIR = BASE_DIR / "data" / "eeg_samples"

print(f"BASE_DIR: {BASE_DIR}")
print(f"DATA_DIR: {DATA_DIR}")

# 初始化 EEGService
init_eeg_service(DATA_DIR)

# 包含路由
app.include_router(analysis_router)
app.include_router(visualization_router)
app.include_router(participants_router)

@app.get("/")
async def root():
    """
    测试API是否正常工作
    """
    return {"message": "EEG分析平台API正在运行"}

@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {
        "status": "healthy",
        "base_dir": str(BASE_DIR),
        "data_dir": str(DATA_DIR)
    }

@app.get("/api/datasets")
async def list_datasets():
    try:
        datasets = []
        for dir_name in os.listdir(DATA_DIR):
            if dir_name.startswith('sub-'):
                eeg_dir = DATA_DIR / dir_name / 'eeg'
                if eeg_dir.exists():
                    # 查找.set文件（EEGLAB格式）
                    set_files = [f for f in os.listdir(eeg_dir) if f.endswith('.set')]
                    for set_file in set_files:
                        # 检查对应的.fdt文件是否存在
                        fdt_file = set_file.replace('.set', '.fdt')
                        if os.path.exists(str(eeg_dir / fdt_file)):
                            # 提取数字ID并转换为整数
                            subject_id = int(dir_name.split('-')[1])
                            datasets.append({
                                "id": subject_id,
                                "name": set_file,
                                "subject": dir_name,
                                "path": str(eeg_dir / set_file),
                                "format": "EEGLAB",
                                "has_fdt": True
                            })
        
        # 按ID数字排序
        datasets.sort(key=lambda x: x["id"])
        return datasets
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}

@app.get("/api/datasets/{dataset_id}/info")
async def get_dataset_info(dataset_id: str):
    try:
        # 找到对应的.set文件
        subject_dir = f"sub-{dataset_id}"
        eeg_dir = DATA_DIR / subject_dir / 'eeg'
        set_files = [f for f in os.listdir(eeg_dir) if f.endswith('.set')]
        
        if not set_files:
            return {"error": "Dataset not found"}
            
        set_file = set_files[0]
        # 设置正确的montage_units
        raw = mne.io.read_raw_eeglab(
            str(eeg_dir / set_file),
            montage_units='cm'  # 或者使用 'm' 如果位置是以米为单位
        )
        
        return {
            "channels": raw.ch_names,
            "sampling_rate": raw.info['sfreq'],
            "duration": raw.times[-1],
            "n_channels": len(raw.ch_names),
            "subject_id": dataset_id
        }
        
    except Exception as e:
        print(f"Error reading dataset: {str(e)}")
        return {"error": str(e)}

@app.get("/api/participants")
async def get_participants():
    try:
        participants_file = "./data/eeg_samples/participants.tsv"
        df = pd.read_csv(participants_file, sep='\t')
        return df.to_dict(orient='records')
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/datasets/{dataset_id}/eeg")
async def get_eeg_data(dataset_id: str, start_time: float = 0, duration: float = 10):
    try:
        subject_dir = f"sub-{dataset_id}"
        eeg_dir = DATA_DIR / subject_dir / 'eeg'
        set_files = [f for f in os.listdir(eeg_dir) if f.endswith('.set')]
        
        if not set_files:
            return {"error": "Dataset not found"}
            
        set_file = set_files[0]
        raw = mne.io.read_raw_eeglab(
            str(eeg_dir / set_file),
            montage_units='cm'
        )
        
        # 获取指定时间范围的数据
        start_idx = int(start_time * raw.info['sfreq'])
        end_idx = int((start_time + duration) * raw.info['sfreq'])
        data, times = raw[:, start_idx:end_idx]
        
        # 构建返回数据
        channel_data = {}
        for i, channel in enumerate(raw.ch_names):
            channel_data[channel] = data[i].tolist()
            
        return {
            "data": channel_data,
            "times": times.tolist(),
            "channels": raw.ch_names,
            "duration": raw.times[-1],
            "sampling_rate": raw.info['sfreq']
        }
        
    except Exception as e:
        print(f"Error reading EEG data: {str(e)}")
        return {"error": str(e)}
