import os
from pathlib import Path

# 路径配置
DATA_DIR = Path("/app/data/eeg_samples")

# Redis配置
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# 缓存配置
CACHE_EXPIRY = 60 * 30  # 默认缓存30分钟
MAX_CACHE_SIZE = 1024 * 1024 * 100  # 默认最大缓存100MB

# 预处理结果缓存键格式
def get_preprocess_cache_key(dataset_id: str, subject_id: str, process_type: str):
    return f"eeg:{dataset_id}:{subject_id}:{process_type}" 