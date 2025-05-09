import numpy as np
from typing import Any, Dict, List, Union, Tuple

def convert_numpy_types(obj: Any) -> Any:
    """
    递归地将NumPy类型转换为Python原生类型，确保JSON序列化安全
    
    Args:
        obj: 任何包含NumPy类型的对象
        
    Returns:
        转换后的对象，所有NumPy类型都被替换为Python原生类型
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj 