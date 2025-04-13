import json
import pickle
from typing import Any, Optional, Dict, Union
import redis

from app.core.config import REDIS_HOST, REDIS_PORT, REDIS_DB, CACHE_EXPIRY

# Redis客户端
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=False
)

# 缓存操作函数
def save_to_cache(key: str, data: Any, expire: int = CACHE_EXPIRY) -> bool:
    """保存数据到缓存
    
    Args:
        key: 缓存键
        data: 要缓存的数据
        expire: 过期时间（秒）
    
    Returns:
        bool: 是否成功缓存
    """
    try:
        # 序列化数据 - 使用pickle能处理更复杂的结构
        serialized_data = pickle.dumps(data)
        
        # 获取数据大小检查是否超限
        data_size = len(serialized_data)
        if data_size > 1024 * 1024 * 50:  # 大于50MB的数据不缓存
            print(f"数据大小 {data_size/1024/1024:.2f}MB 超过单次缓存限制，跳过缓存")
            return False
            
        # 保存到Redis，设置过期时间
        redis_client.set(key, serialized_data, ex=expire)
        return True
    except Exception as e:
        print(f"缓存数据失败: {str(e)}")
        return False

def get_from_cache(key: str) -> Optional[Any]:
    """从缓存获取数据
    
    Args:
        key: 缓存键
    
    Returns:
        缓存的数据或None
    """
    try:
        data = redis_client.get(key)
        if data:
            # 反序列化
            return pickle.loads(data)
        return None
    except Exception as e:
        print(f"获取缓存数据失败: {str(e)}")
        return None

def save_metadata(key: str, metadata: Dict, expire: int = CACHE_EXPIRY * 2) -> bool:
    """保存元数据到缓存
    
    Args:
        key: 元数据键名 (通常是{data_key}:meta)
        metadata: 元数据字典
        expire: 过期时间（秒）
    
    Returns:
        bool: 是否成功缓存
    """
    try:
        # 元数据使用JSON格式存储更轻量
        redis_client.set(key, json.dumps(metadata), ex=expire)
        return True
    except Exception as e:
        print(f"保存元数据失败: {str(e)}")
        return False

def get_metadata(key: str) -> Optional[Dict]:
    """获取元数据
    
    Args:
        key: 元数据键名
    
    Returns:
        Dict: 元数据或None
    """
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        print(f"获取元数据失败: {str(e)}")
        return None

def delete_cache(key_pattern: str) -> int:
    """删除匹配模式的缓存
    
    Args:
        key_pattern: 键模式，如 "eeg:dataset1:*"
    
    Returns:
        int: 删除的键数量
    """
    try:
        keys = redis_client.keys(key_pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        print(f"删除缓存失败: {str(e)}")
        return 0

def check_redis_connection() -> bool:
    """检查Redis连接是否正常
    
    Returns:
        bool: 连接是否成功
    """
    try:
        return redis_client.ping()
    except Exception as e:
        print(f"Redis连接失败: {str(e)}")
        return False 