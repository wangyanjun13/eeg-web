import os
import json
import uuid
import time
import numpy as np
import scipy.io as sio
import traceback
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any, Union, Tuple

class UploadService:
    """
    上传服务类，用于管理上传文件的元数据
    """
    def __init__(self):
        # 确保元数据目录存在
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.metadata_dir = Path(os.path.join(base_dir, "uploads/metadata"))
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # 元数据文件路径
        self.metadata_file = self.metadata_dir / "files_metadata.json"
        print(f"元数据文件路径: {self.metadata_file}")
        
        # 如果元数据文件不存在，创建一个空的JSON文件
        if not self.metadata_file.exists():
            print(f"元数据文件不存在，创建新文件")
            with open(self.metadata_file, "w") as f:
                json.dump([], f)
    
    def _load_metadata(self) -> List[Dict[str, Any]]:
        """加载所有文件元数据"""
        try:
            with open(self.metadata_file, "r") as f:
                data = json.load(f)
                print(f"从元数据文件加载了 {len(data)} 个文件记录")
                return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"加载元数据文件失败: {str(e)}")
            return []
    
    def _save_metadata(self, metadata: List[Dict[str, Any]]) -> None:
        """保存所有文件元数据"""
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
    
    def save_file_metadata(self, file_metadata: Dict[str, Any]) -> str:
        """
        保存单个文件的元数据
        
        Args:
            file_metadata: 文件元数据字典
        
        Returns:
            str: 生成的文件ID
        """
        metadata = self._load_metadata()
        
        # 生成唯一ID
        file_id = str(uuid.uuid4())
        file_metadata["id"] = file_id
        
        # 添加到元数据列表
        metadata.append(file_metadata)
        
        # 保存更新后的元数据
        self._save_metadata(metadata)
        
        return file_id
    
    def get_files(self, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取所有文件的元数据，可以按文件类型筛选
        
        Args:
            file_type: 可选的文件类型筛选条件，"data"或"model"
        
        Returns:
            List[Dict[str, Any]]: 文件元数据列表
        """
        metadata = self._load_metadata()
        
        if file_type:
            metadata = [item for item in metadata if item.get("file_type") == file_type]
        
        # 按上传时间降序排序
        metadata.sort(key=lambda x: x.get("upload_time", ""), reverse=True)
        
        return metadata
    
    def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取特定文件的元数据
        
        Args:
            file_id: 文件ID
        
        Returns:
            Optional[Dict[str, Any]]: 文件元数据，如果不存在则返回None
        """
        metadata = self._load_metadata()
        
        for item in metadata:
            if item.get("id") == file_id:
                return item
        
        return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        删除文件及其元数据
        
        Args:
            file_id: 文件ID
        
        Returns:
            bool: 删除是否成功
        """
        metadata = self._load_metadata()
        
        # 查找文件元数据
        file_metadata = None
        file_index = -1
        
        for i, item in enumerate(metadata):
            if item.get("id") == file_id:
                file_metadata = item
                file_index = i
                break
        
        # 如果文件不存在
        if file_index == -1:
            return False
        
        # 删除物理文件
        try:
            file_path = file_metadata.get("file_path")
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"删除文件时出错: {e}")
            return False
        
        # 从元数据列表中移除
        metadata.pop(file_index)
        
        # 保存更新后的元数据
        self._save_metadata(metadata)
        
        return True


class ModelEvaluationService:
    """
    模型评估服务类，用于评估模型对EEG数据的处理效果
    """
    def __init__(self, upload_service: UploadService):
        self.upload_service = upload_service
    
    def evaluate_model(self, data_file_id: str, model_file_id: str) -> Dict[str, Any]:
        """
        评估模型对EEG数据的处理效果
        
        Args:
            data_file_id: 数据文件ID
            model_file_id: 模型文件ID
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        try:
            # 导入必要的库
            try:
                import tensorflow as tf
                import tensorflow.keras.losses
                from sklearn.metrics import mean_squared_error, mean_absolute_error
            except ImportError as e:
                return {
                    "status": "error",
                    "error_type": "import_error",
                    "message": f"导入必要库失败: {str(e)}"
                }
            
            # 确认损失函数是否能直接访问
            try:
                print("检查TensorFlow环境...")
                print(f"TensorFlow版本: {tf.__version__}")
                print(f"Keras版本: {tf.keras.__version__ if hasattr(tf.keras, '__version__') else '内置于TF'}")
                print("可用的损失函数:", dir(tf.keras.losses))
            except Exception as tf_check_err:
                print(f"TensorFlow环境检查失败: {str(tf_check_err)}")
            
            start_time = time.time()  # 记录开始时间
            
            # 获取数据文件信息
            data_file = self.upload_service.get_file_by_id(data_file_id)
            if not data_file:
                return {
                    "status": "error",
                    "error_type": "file_not_found",
                    "message": f"找不到ID为 {data_file_id} 的数据文件"
                }
            
            # 获取模型文件信息
            model_file = self.upload_service.get_file_by_id(model_file_id)
            if not model_file:
                return {
                    "status": "error",
                    "error_type": "file_not_found",
                    "message": f"找不到ID为 {model_file_id} 的模型文件"
                }
            
            # 使用文件的实际存储路径
            data_file_path = data_file["file_path"]
            model_file_path = model_file["file_path"]
            
            if not os.path.exists(data_file_path):
                return {
                    "status": "error",
                    "error_type": "file_not_found",
                    "message": f"数据文件 {data_file['original_filename']} 不存在于服务器存储中"
                }
            
            if not os.path.exists(model_file_path):
                return {
                    "status": "error",
                    "error_type": "file_not_found",
                    "message": f"模型文件 {model_file['original_filename']} 不存在于服务器存储中"
                }
            
            print(f"开始处理数据文件 {data_file['original_filename']} 和模型文件 {model_file['original_filename']}")
            
            # 加载EEG数据
            eeg_data, channel_names, sampling_rate = self._load_eeg_data(data_file_path, data_file['original_filename'])
            
            # 如果找不到数据
            if eeg_data is None:
                return {
                    "status": "error",
                    "error_type": "data_not_found",
                    "message": "无法从文件中提取EEG数据",
                    "details": {
                        "data_file": data_file['original_filename'],
                        "model_file": model_file['original_filename']
                    }
                }
            
            # 创建原始数据的样本（用于可视化）
            original_sample = eeg_data[:, :min(1000, eeg_data.shape[1])].tolist()
            
            # 加载模型
            try:
                model, is_fcnn_model, expected_input_size, is_cnn_model = self._load_model(model_file_path)
            except Exception as e:
                error_msg = str(e)
                print(f"加载模型时出错: {error_msg}")
                traceback.print_exc()
                
                # 提供一个更有帮助的错误消息
                friendly_error = error_msg
                if "mean_squared_error" in error_msg:
                    friendly_error = "模型使用了特定的损失函数'mean_squared_error'，但当前环境无法加载。建议重新保存模型时不包含编译信息。"
                elif "BasicBlockall" in error_msg:
                    friendly_error = "模型使用了自定义层'BasicBlockall'，需要特定的加载环境。"
                elif "Unknown layer" in error_msg:
                    friendly_error = "模型使用了未知的自定义层，需要对应的Layer类定义。建议使用标准层重新构建模型。"
                elif "unable to open file" in error_msg:
                    friendly_error = "无法打开模型文件，文件可能已损坏或格式不兼容。"
                
                return {
                    "status": "error",
                    "error_type": "model_loading_error",
                    "message": f"加载模型时出错: {friendly_error}",
                    "details": {
                        "data_file": data_file['original_filename'],
                        "model_file": model_file['original_filename'],
                        "original_data": {
                            "channels": channel_names,
                            "shape": list(eeg_data.shape),
                            "sample": original_sample[:5] if len(original_sample) > 5 else original_sample
                        },
                        "technical_error": error_msg
                    }
                }
            
            # 处理EEG数据并进行模型评估
            try:
                # 准备模型输入
                model_input = self._prepare_model_input(
                    eeg_data, 
                    model, 
                    is_fcnn_model, 
                    expected_input_size, 
                    is_cnn_model, 
                    data_file['original_filename']
                )
                
                if model_input is None:
                    return {
                        "status": "error",
                        "error_type": "input_preparation_error",
                        "message": "无法准备适合模型的输入数据",
                        "details": {
                            "data_file": data_file['original_filename'],
                            "model_file": model_file['original_filename'],
                            "data_shape": str(eeg_data.shape)
                        }
                    }
                
                # 使用安全预测函数
                model_output, error_response = self._safe_model_predict(model, model_input, data_file, model_file)
                
                # 如果预测出错，直接返回错误响应
                if error_response is not None:
                    return error_response
                
                # 将模型输出转换回EEG数据格式
                processed_eeg_data = self._process_model_output(
                    model_output, 
                    eeg_data, 
                    channel_names, 
                    is_cnn_model, 
                    data_file, 
                    model_file, 
                    original_sample
                )
                
                # 如果处理失败
                if isinstance(processed_eeg_data, dict) and processed_eeg_data.get("status") == "error":
                    return processed_eeg_data
                
                # 检查形状是否匹配
                if processed_eeg_data.shape != eeg_data.shape:
                    print(f"警告: 处理后的EEG数据形状 {processed_eeg_data.shape} 与原始数据形状 {eeg_data.shape} 不匹配")
                    return {
                        "status": "error",
                        "error_type": "shape_mismatch",
                        "message": f"模型输出形状 {processed_eeg_data.shape} 与输入数据形状 {eeg_data.shape} 不匹配",
                        "details": {
                            "input_shape": str(eeg_data.shape),
                            "output_shape": str(processed_eeg_data.shape),
                            "data_file": data_file['original_filename'],
                            "model_file": model_file['original_filename'],
                            "original_data": {
                                "channels": channel_names,
                                "shape": list(eeg_data.shape),
                                "sample": original_sample[:5] if len(original_sample) > 5 else original_sample
                            },
                            "model_output_sample": processed_eeg_data[:, :5].tolist() if processed_eeg_data.shape[1] >= 5 else processed_eeg_data.tolist()
                        }
                    }
                
                # 计算评估指标
                return self._calculate_metrics(
                    eeg_data, 
                    processed_eeg_data, 
                    channel_names, 
                    sampling_rate, 
                    original_sample, 
                    start_time, 
                    data_file, 
                    model_file
                )
                
            except Exception as e:
                print(f"使用模型处理数据时出错: {str(e)}")
                traceback.print_exc()
                return {
                    "status": "error",
                    "error_type": "processing_error",
                    "message": f"使用模型处理数据时出错: {str(e)}",
                    "details": {
                        "data_file": data_file['original_filename'],
                        "model_file": model_file['original_filename'],
                        "original_data": {
                            "channels": channel_names,
                            "shape": list(eeg_data.shape),
                            "sample": original_sample[:5] if len(original_sample) > 5 else original_sample
                        }
                    }
                }
        except Exception as e:
            print(f"评估模型时出错: {str(e)}")
            traceback.print_exc()
            return {
                "status": "error",
                "error_type": "general_error",
                "message": f"处理文件时出错: {str(e)}"
            }
    
    def _load_eeg_data(self, file_path: str, file_name: str) -> Tuple[Optional[np.ndarray], List[str], float]:
        """
        加载EEG数据
        
        Args:
            file_path: 文件路径
            file_name: 文件名
            
        Returns:
            Tuple[Optional[np.ndarray], List[str], float]: EEG数据、通道名称、采样率
        """
        eeg_data = None
        channel_names = []
        sampling_rate = 250  # 默认采样率
        
        # 处理.mat文件
        if file_name.endswith('.mat'):
            try:
                mat_data = sio.loadmat(file_path)
                print(f"加载的.mat文件包含键: {list(mat_data.keys())}")
                
                # 尝试查找EEG数据数组
                for key in mat_data.keys():
                    if key.startswith('__'):  # 跳过元数据
                        continue
                    if isinstance(mat_data[key], np.ndarray) and len(mat_data[key].shape) >= 2:
                        if eeg_data is None or (mat_data[key].shape[0] <= 128 and mat_data[key].shape[1] > mat_data[key].shape[0]):
                            eeg_data = mat_data[key]
                            print(f"从.mat文件中提取了EEG数据数组，键: {key}, 形状: {eeg_data.shape}")
                
                # 如果找不到，尝试加载较大的数组作为潜在数据
                if eeg_data is None:
                    largest_array = None
                    largest_size = 0
                    for key in mat_data.keys():
                        if key.startswith('__'):  # 跳过元数据
                            continue
                        if isinstance(mat_data[key], np.ndarray) and len(mat_data[key].shape) >= 2:
                            array_size = np.prod(mat_data[key].shape)
                            if array_size > largest_size:
                                largest_array = mat_data[key]
                                largest_size = array_size
                    
                    if largest_array is not None:
                        eeg_data = largest_array
                        print(f"使用最大数组作为EEG数据，形状: {eeg_data.shape}")
                
                # 尝试从.mat文件中提取通道名称
                if 'channels' in mat_data and isinstance(mat_data['channels'], np.ndarray):
                    try:
                        channel_names = [str(ch[0]) if isinstance(ch, np.ndarray) else str(ch) for ch in mat_data['channels']]
                    except:
                        pass
                elif 'chanlocs' in mat_data and isinstance(mat_data['chanlocs'], np.ndarray):
                    try:
                        channel_names = [str(chan[0]) for chan in mat_data['chanlocs']]
                    except:
                        pass
                
                # 尝试获取采样率
                if 'fs' in mat_data and np.isscalar(mat_data['fs']):
                    sampling_rate = float(mat_data['fs'])
                elif 'srate' in mat_data and np.isscalar(mat_data['srate']):
                    sampling_rate = float(mat_data['srate'])
                elif 'sfreq' in mat_data and np.isscalar(mat_data['sfreq']):
                    sampling_rate = float(mat_data['sfreq'])
                elif 'sampling_rate' in mat_data and np.isscalar(mat_data['sampling_rate']):
                    sampling_rate = float(mat_data['sampling_rate'])
            except Exception as e:
                print(f"加载.mat文件时出错: {str(e)}")
                return None, [], sampling_rate
                
        # 处理.npy文件
        elif file_name.endswith('.npy'):
            try:
                eeg_data = np.load(file_path)
                print(f"从.npy文件中加载了EEG数据，形状: {eeg_data.shape}")
            except Exception as e:
                print(f"加载.npy文件时出错: {str(e)}")
                return None, [], sampling_rate
        
        # 如果找不到数据
        if eeg_data is None:
            return None, [], sampling_rate
        
        # 标准化数据格式：[通道数, 时间点数]
        if len(eeg_data.shape) > 2:
            # 对于3D或更高维度数据，取第一个试验/样本
            print(f"发现高维数据，形状: {eeg_data.shape}，提取第一个样本")
            eeg_data = eeg_data[0]
            print(f"提取后形状: {eeg_data.shape}")
        
        # 如果数据是时间点×通道格式，转置为通道×时间点
        # 使用更智能的检测逻辑
        print(f"原始数据形状: {eeg_data.shape}")
        
        # 检查文件名中是否包含EMG或epochs提示
        is_special_format = False
        if "EMG" in file_name or "epochs" in file_name:
            is_special_format = True
            print(f"检测到特殊数据格式: {file_name}")
        
        # 智能检测数据结构
        if is_special_format and eeg_data.shape[0] > 512 and eeg_data.shape[1] == 512:
            # 特殊情况: EMG_all_epochs.mat 数据(5598, 512)
            # 这种情况，第一维可能是时间点*通道或样本数，第二维是特征
            print(f"特殊数据格式: 可能是多样本数据，样本数: {eeg_data.shape[0]}, 特征数: {eeg_data.shape[1]}")
            # 为简单起见，我们只使用第一个样本
            first_sample = eeg_data[0:1, :]
            print(f"选择第一个样本作为输入，形状: {first_sample.shape}")
            eeg_data = first_sample
        elif eeg_data.shape[0] > eeg_data.shape[1] and eeg_data.shape[1] <= 128:
            eeg_data = eeg_data.T
            print(f"转置数据为通道×时间点格式，新形状: {eeg_data.shape}")
        
        # 确保我们有适当的通道名称
        if not channel_names or len(channel_names) != eeg_data.shape[0]:
            channel_names = [f"Channel {i+1}" for i in range(eeg_data.shape[0])]
            print(f"生成了 {len(channel_names)} 个默认通道名称")
        
        # 打印数据统计信息以进行验证
        print(f"最终EEG数据形状: {eeg_data.shape}, 通道数: {len(channel_names)}, 采样率: {sampling_rate}Hz")
        
        return eeg_data, channel_names, sampling_rate

    def _load_model(self, model_file_path: str) -> Tuple[Any, bool, Optional[int], bool]:
        """
        加载模型并检测模型类型
        
        Args:
            model_file_path: 模型文件路径
            
        Returns:
            Tuple[Any, bool, Optional[int], bool]: 模型、是否为fcNN模型、期望的输入大小、是否为CNN模型
        """
        import tensorflow as tf
        
        # 定义通用自定义层
        class CustomLayer(tf.keras.layers.Layer):
            def __init__(self, **kwargs):
                super(CustomLayer, self).__init__(**kwargs)
            
            def call(self, inputs, **kwargs):
                return inputs
            
            def get_config(self):
                return super(CustomLayer, self).get_config()
        
        # 使用自定义层定义
        class BasicBlockall(tf.keras.layers.Layer):
            def __init__(self, **kwargs):
                super(BasicBlockall, self).__init__(**kwargs)
            
            def build(self, input_shape):
                super(BasicBlockall, self).build(input_shape)
            
            def call(self, inputs):
                return inputs
            
            def get_config(self):
                config = super(BasicBlockall, self).get_config()
                return config
        
        # 定义损失函数 - 直接使用TensorFlow函数而不是导入
        def mse(y_true, y_pred):
            return tf.reduce_mean(tf.square(y_true - y_pred))
        
        def mean_squared_error(y_true, y_pred):
            return tf.reduce_mean(tf.square(y_true - y_pred))
        
        # 创建更多损失函数和自定义层的缓存
        custom_functions = {}
        
        # 所有可能的自定义层名称
        custom_layer_names = [
            "BasicBlockall", "CustomConv", "BasicBlock", "Attention", 
            "SelfAttention", "ResidualBlock", "TCN", "GRU", 
            "BiLSTM", "CausalConv1D"
        ]
        
        # 为每个可能的自定义层创建一个通用实现
        for layer_name in custom_layer_names:
            class_def = type(layer_name, (CustomLayer,), {})
            custom_functions[layer_name] = class_def
        
        # 简化自定义对象集合
        custom_objects = {
            "BasicBlockall": BasicBlockall,
            "mse": mse,
            "mean_squared_error": mean_squared_error,
            "MeanSquaredError": tf.keras.losses.MeanSquaredError,
            "MSE": tf.keras.losses.MeanSquaredError,
        }
        
        # 添加所有通用自定义层
        custom_objects.update(custom_functions)
        
        print(f"尝试加载模型: {model_file_path}")
        print(f"已注册的自定义对象: {list(custom_objects.keys())}")
        
        # 加载模型 - 使用compile=False避免编译时的问题
        with tf.keras.utils.custom_object_scope(custom_objects):
            try:
                print("使用标准方式加载模型...")
                model = tf.keras.models.load_model(model_file_path, compile=False)
            except Exception as model_err:
                print(f"首次尝试加载模型失败: {str(model_err)}")
                # 尝试直接加载为SavedModel
                try:
                    print("尝试使用SavedModel方式加载...")
                    model = tf.saved_model.load(model_file_path)
                    print("使用SavedModel加载成功")
                except Exception as saved_err:
                    print(f"SavedModel加载失败: {str(saved_err)}")
                    # 最后尝试使用自定义方式
                    print("尝试最终兼容性方案...")
                    
                    # 动态识别需要的自定义层
                    error_msg = str(model_err)
                    if "Unknown layer" in error_msg:
                        import re
                        # 尝试从错误信息中提取层名称
                        match = re.search(r"Unknown layer: '([^']+)'", error_msg)
                        if match:
                            layer_name = match.group(1)
                            print(f"检测到未知层: {layer_name}，动态添加")
                            
                            # 动态创建层并添加到custom_objects
                            new_layer = type(layer_name, (CustomLayer,), {})
                            custom_objects[layer_name] = new_layer
                    
                    # 最后尝试
                    model = tf.keras.models.load_model(
                        model_file_path, 
                        custom_objects=custom_objects,
                        compile=False
                    )
        
        print(f"模型已成功加载，输入形状: {model.input_shape}, 输出形状: {model.output_shape}")
        model.summary(print_fn=print)

        # 检查模型是否为特殊的fcNN结构（第一层是Dense层）
        is_fcnn_model = False
        expected_input_size = None
        try:
            if len(model.layers) > 0:
                first_layer = model.layers[0]
                if isinstance(first_layer, tf.keras.layers.Dense):
                    is_fcnn_model = True
                    expected_input_size = first_layer.input_shape[-1]
                    print(f"检测到fcNN模型结构，期望的输入维度: {expected_input_size}")
        except Exception as e:
            print(f"检查模型结构时出错: {str(e)}")
        
        # 检测是否为CNN模型（通过查看第一层是否为Conv1D或Conv2D）
        is_cnn_model = False
        try:
            first_layer = model.layers[0]
            if "Conv" in first_layer.__class__.__name__:
                is_cnn_model = True
                print(f"检测到CNN模型，第一层: {first_layer.__class__.__name__}")
        except Exception as e:
            print(f"检查模型第一层时出错: {str(e)}")
        
        return model, is_fcnn_model, expected_input_size, is_cnn_model
    
    def _safe_model_predict(self, model, model_input, data_file, model_file):
        """
        安全地执行模型预测，处理各种可能的错误
        
        Args:
            model: 模型对象
            model_input: 模型输入数据
            data_file: 数据文件信息
            model_file: 模型文件信息
            
        Returns:
            Tuple[np.ndarray, Dict[str, Any]]: 模型输出和错误响应（如果有错误）
        """
        try:
            print(f"开始使用模型预测，输入形状: {model_input.shape}, 数据类型: {model_input.dtype}")
            print(f"模型输入示例值: {model_input[0, :5] if model_input.shape[1] >= 5 else model_input}")
            
            # 检查是否有NaN或无穷大值
            if np.isnan(model_input).any() or np.isinf(model_input).any():
                print("警告: 输入数据中包含NaN或无穷大值，将被替换为0")
                model_input = np.nan_to_num(model_input, nan=0.0, posinf=0.0, neginf=0.0)
            
            # 执行预测
            model_output = model.predict(model_input)
            print(f"模型预测成功，输出形状: {model_output.shape}")
            return model_output, None
        except ValueError as ve:
            # 形状不匹配错误，通常是输入维度不符合模型期望
            error_msg = str(ve)
            print(f"模型预测时值错误: {error_msg}")
            
            # 尝试从错误消息中提取更详细的信息
            shape_mismatch = "is incompatible with the layer" in error_msg
            
            if shape_mismatch:
                # 尝试直接从模型获取输入层信息
                try:
                    expected_shape = str(model.layers[0].input_shape)
                    print(f"模型第一层期望的输入形状: {expected_shape}")
                except:
                    expected_shape = "未知"
                
                error_response = {
                    "status": "error",
                    "error_type": "shape_mismatch",
                    "message": f"模型输入形状不匹配: {error_msg}",
                    "details": {
                        "input_shape": str(model_input.shape),
                        "expected_shape": expected_shape,
                        "data_file": data_file['original_filename'],
                        "model_file": model_file['original_filename'],
                        "error_message": error_msg
                    }
                }
            else:
                # 其他值错误
                error_response = {
                    "status": "error",
                    "error_type": "processing_error",
                    "message": f"模型处理数据时出现值错误: {error_msg}",
                    "details": {
                        "data_file": data_file['original_filename'],
                        "model_file": model_file['original_filename'],
                        "input_shape": str(model_input.shape)
                    }
                }
            return None, error_response
        except Exception as e:
            import tensorflow as tf
            # 检测TensorFlow特有错误
            if isinstance(e, tf.errors.InvalidArgumentError):
                # TensorFlow特定的参数错误
                error_msg = str(e)
                print(f"TensorFlow参数错误: {error_msg}")
                error_response = {
                    "status": "error",
                    "error_type": "tensorflow_error",
                    "message": f"TensorFlow模型执行错误: {error_msg}",
                    "details": {
                        "data_file": data_file['original_filename'],
                        "model_file": model_file['original_filename'],
                        "input_shape": str(model_input.shape)
                    }
                }
            else:
                # 其他未预期的错误
                error_msg = str(e)
                print(f"模型预测时发生未知错误: {error_msg}")
                traceback.print_exc()
                error_response = {
                    "status": "error",
                    "error_type": "processing_error",
                    "message": f"使用模型处理数据时出错: {error_msg}",
                    "details": {
                        "data_file": data_file['original_filename'],
                        "model_file": model_file['original_filename'],
                        "input_shape": str(model_input.shape)
                    }
                }
            return None, error_response
    
    def _prepare_model_input(self, eeg_data, model, is_fcnn_model, expected_input_size, is_cnn_model, file_name):
        """
        准备模型输入数据
        
        Args:
            eeg_data: EEG数据
            model: 模型对象
            is_fcnn_model: 是否为fcNN模型
            expected_input_size: 期望的输入大小
            is_cnn_model: 是否为CNN模型
            file_name: 文件名
            
        Returns:
            np.ndarray: 准备好的模型输入数据
        """
        # 检查模型输入形状
        model_input_shape = model.input_shape
        if model_input_shape[0] is None:  # 批次维度
            model_input_shape = model_input_shape[1:]
        
        # 打印模型输入形状以便调试
        print(f"模型期望的输入形状: {model.input_shape}")
        
        # 准备适合模型的输入格式
        model_input = None
        
        # 为fcNN模型特殊处理
        if is_fcnn_model and expected_input_size is not None:
            print(f"为fcNN模型准备输入，需要的维度: {expected_input_size}")
            
            # 如果原始数据是单通道EEG，可能需要特殊处理
            print(f"原始EEG数据形状: {eeg_data.shape}")
            
            # 强制将数据展平为一维
            flat_data = eeg_data.flatten()
            print(f"扁平化后形状: {flat_data.shape}, 共{len(flat_data)}个元素")
            
            # 计算需要扩展多少倍数据
            if len(flat_data) < expected_input_size:
                repeats_needed = int(np.ceil(expected_input_size / len(flat_data)))
                print(f"数据不足，需要重复{repeats_needed}次")
                
                # 创建重复数据
                expanded_data = np.tile(flat_data, repeats_needed)
                # 截断到精确大小
                final_input = expanded_data[:expected_input_size]
            else:
                # 如果数据足够，直接取或填充至精确大小
                if len(flat_data) > expected_input_size:
                    final_input = flat_data[:expected_input_size]
                else:
                    final_input = flat_data
            
            # 确认数据大小正确
            if len(final_input) != expected_input_size:
                print(f"无法准备符合要求的数据: 期望{expected_input_size}，实际{len(final_input)}")
                return None
            
            # 重塑为模型期望的精确输入形状: (batch_size, features)
            model_input = final_input.reshape(1, expected_input_size)
            
            print(f"准备完成，最终输入形状: {model_input.shape}，数据类型: {model_input.dtype}")
            
            # 验证形状
            if model_input.shape != (1, expected_input_size):
                print(f"警告：形状不匹配！期望(1, {expected_input_size})，得到{model_input.shape}")
                # 最后尝试强制转换形状
                try:
                    model_input = np.reshape(model_input, (1, expected_input_size))
                    print(f"强制转换后形状: {model_input.shape}")
                except Exception as reshape_error:
                    print(f"强制转换形状失败: {str(reshape_error)}")
                    return None
        elif is_cnn_model:
            # CNN模型特殊处理，确保输入形状为(batch_size, time_steps, features)
            print(f"为CNN模型准备输入，原始数据形状: {eeg_data.shape}")
            
            # 检查是否为Simple_CNN类型的模型(检查输入形状为(None, 512, 1)或类似)
            is_simple_cnn = False
            if model.input_shape[1] is not None and model.input_shape[2] == 1:
                is_simple_cnn = True
                print(f"检测到Simple_CNN类型模型，期望输入形状: {model.input_shape}")
            
            # 专门处理EMG_all_epochs.mat这样的数据
            if "EMG" in file_name or "epochs" in file_name:
                print("处理特殊EMG/epochs数据格式")
                
                # 如果是(1, 512)这样的数据，直接reshape为(1, 512, 1)用于Simple_CNN
                if is_simple_cnn and eeg_data.shape[0] == 1 and eeg_data.shape[1] == model.input_shape[1]:
                    print(f"将数据重塑为Simple_CNN输入格式")
                    model_input = eeg_data.reshape(1, eeg_data.shape[1], 1)
                    print(f"重塑后形状: {model_input.shape}")
                else:
                    print(f"检查匹配项: is_simple_cnn={is_simple_cnn}, shape={eeg_data.shape}, expected={model.input_shape[1] if model.input_shape[1] is not None else 'None'}")
                    
                    # 验证数据维度匹配模型
                    if model.input_shape[1] is not None:
                        time_dim = model.input_shape[1]
                        # 如果数据时间维度不匹配模型，尝试调整
                        if eeg_data.shape[1] != time_dim:
                            print(f"调整数据时间维度从 {eeg_data.shape[1]} 到 {time_dim}")
                            resized_data = np.zeros((eeg_data.shape[0], time_dim))
                            min_time = min(eeg_data.shape[1], time_dim)
                            resized_data[:, :min_time] = eeg_data[:, :min_time]
                            eeg_data = resized_data
                            print(f"调整后形状: {eeg_data.shape}")
                    
                    # 对于Single_CNN，使用第一个样本的数据
                    if is_simple_cnn:
                        channel_data = eeg_data[0, :].reshape(1, eeg_data.shape[1], 1)
                        model_input = channel_data
                        print(f"为Simple_CNN创建单通道输入，形状: {model_input.shape}")
            # 检查是否需要转置，确保第二维是时间步
            elif eeg_data.shape[0] > eeg_data.shape[1]:  # 如果通道数比时间步多
                # 对于 (5598, 512) 这样的数据，我们需要选择适当的通道子集
                # 这里假设这是多通道数据，采样了很多个通道
                # 选择前64个通道（或更少如果通道数小于64）
                num_channels = min(64, eeg_data.shape[0])
                print(f"选择前{num_channels}个通道")
                selected_data = eeg_data[:num_channels, :]
                
                # 对于CNN模型，我们需要reshape为(batch_size, time_steps, channels)
                # 这里我们将通道维度放在最后
                # 对于Simple_CNN模型，期望输入为(batch, time_steps, 1)
                if model.input_shape[-1] == 1:
                    # 处理单通道输入情况
                    # 为每个通道创建单独的样本
                    samples = []
                    for i in range(selected_data.shape[0]):
                        # 将每个通道数据形状转换为(1, time_steps, 1)
                        channel_data = selected_data[i, :].reshape(1, selected_data.shape[1], 1)
                        samples.append(channel_data)
                    
                    # 只使用第一个通道作为示例（可以修改为使用所有通道批处理）
                    model_input = samples[0]
                    print(f"已创建单通道CNN输入，形状: {model_input.shape}")
                else:
                    # 处理多通道输入情况
                    # 将所有通道作为特征维度
                    model_input = selected_data.T.reshape(1, selected_data.shape[1], selected_data.shape[0])
                    print(f"已创建多通道CNN输入，形状: {model_input.shape}")
            else:
                # 如果数据已经是(通道较少, 时间步较多)的形状
                # 确保时间维度正确
                time_dim = eeg_data.shape[1]
                channel_dim = eeg_data.shape[0]
                
                # 对于模型期望(None, 512, 1)的情况
                if model.input_shape[1] == time_dim and model.input_shape[2] == 1:
                    # 单通道情况 - 只使用第一个通道
                    model_input = eeg_data[0, :].reshape(1, time_dim, 1)
                    print(f"使用第一个通道数据，形状: {model_input.shape}")
                else:
                    # 多通道情况 - 使用所有通道
                    model_input = eeg_data.T.reshape(1, time_dim, channel_dim)
                    print(f"使用所有通道数据，形状: {model_input.shape}")
        else:
            # 普通模型处理逻辑
            # 尝试不同的输入形状准备方法
            if len(model_input_shape) == 2:  # [通道，时间点]
                if model_input_shape[0] is None or model_input_shape[0] == eeg_data.shape[0]:
                    # 模型期望通道×时间点格式
                    model_input = eeg_data
                    if model_input_shape[1] is not None and model_input_shape[1] != eeg_data.shape[1]:
                        # 需要调整时间点数量
                        model_input = np.zeros((eeg_data.shape[0], model_input_shape[1]))
                        min_length = min(eeg_data.shape[1], model_input_shape[1])
                        model_input[:, :min_length] = eeg_data[:, :min_length]
                else:
                    # 可能是批次×特征格式，尝试重塑数据
                    model_input = eeg_data.reshape(1, -1)[:, :model_input_shape[1]] if model_input_shape[1] is not None else eeg_data.reshape(1, -1)
            elif len(model_input_shape) == 3:  # [批次，通道，时间点] or [批次，时间点，通道]
                # 尝试两种格式
                if model_input_shape[1] == eeg_data.shape[0]:
                    # 批次×通道×时间点
                    model_input = np.expand_dims(eeg_data, 0)
                else:
                    # 批次×时间点×通道
                    model_input = np.expand_dims(eeg_data.T, 0)
            elif len(model_input_shape) == 1:  # [特征]
                # 可能是一个扁平化输入
                model_input = eeg_data.reshape(-1)[:model_input_shape[0]] if model_input_shape[0] is not None else eeg_data.reshape(-1)
                model_input = np.expand_dims(model_input, 0)
            
            # 处理特殊情况：输入维度为32768的模型（可能是用户上传的特殊模型）
            # 这种情况下，我们需要尝试将数据重塑为适合该模型的输入
            if model_input is None or (
                hasattr(model, 'input_shape') and 
                len(model.input_shape) > 1 and 
                model.input_shape[1] == 32768 and
                model_input.shape[-1] != 32768
            ):
                print(f"检测到特殊输入大小模型：期望32768，正在尝试适配...")
                # 获取总元素数
                total_elements = np.prod(eeg_data.shape)
                
                if total_elements < 32768:
                    # 如果元素不够，使用重复或填充
                    repeats = int(np.ceil(32768 / total_elements))
                    flat_data = np.tile(eeg_data.flatten(), repeats)[:32768]
                    model_input = np.expand_dims(flat_data, 0)
                    print(f"数据元素不足，使用重复填充至32768，形状: {model_input.shape}")
                else:
                    # 如果元素足够，直接重塑
                    flat_data = eeg_data.flatten()[:32768]
                    model_input = np.expand_dims(flat_data, 0)
                    print(f"数据重塑为32768，形状: {model_input.shape}")
        
        if model_input is None:
            print(f"无法准备适合模型输入形状 {model_input_shape} 的数据")
            return None
        
        print(f"准备模型输入，形状: {model_input.shape}")
        
        # 添加数据类型检查和转换
        if model_input.dtype != np.float32:
            print(f"将输入数据从 {model_input.dtype} 转换为 float32")
            model_input = model_input.astype(np.float32)
        
        return model_input

    def _process_model_output(self, model_output, eeg_data, channel_names, is_cnn_model, data_file, model_file, original_sample):
        """
        处理模型输出数据，转换为标准EEG格式
        
        Args:
            model_output: 模型输出数据
            eeg_data: 原始EEG数据
            channel_names: 通道名称
            is_cnn_model: 是否为CNN模型
            data_file: 数据文件信息
            model_file: 模型文件信息
            original_sample: 原始数据样本
            
        Returns:
            Union[np.ndarray, Dict[str, Any]]: 处理后的EEG数据或错误响应
        """
        print(f"处理模型输出，形状: {model_output.shape}")
        
        # 将模型输出转换回EEG数据格式 [通道，时间点]
        if len(model_output.shape) == 3 and model_output.shape[0] == 1:
            # 批次×通道×时间点 或 批次×时间点×通道
            if model_output.shape[1] == len(channel_names):
                # 批次×通道×时间点
                processed_eeg_data = model_output[0]
            elif model_output.shape[2] == len(channel_names):
                # 批次×时间点×通道
                processed_eeg_data = model_output[0].T
            else:
                # CNN模型可能输出与输入通道数不匹配的结果
                # 例如，一个单通道CNN模型(batch, time_steps, 1)处理多通道数据
                if is_cnn_model and model_output.shape[2] == 1:
                    print(f"CNN模型输出单通道数据，将复制到所有通道")
                    # 将单通道输出复制到所有通道
                    processed_eeg_data = np.zeros((len(channel_names), model_output.shape[1]))
                    # 复制单通道输出到所有通道
                    for i in range(len(channel_names)):
                        processed_eeg_data[i, :] = model_output[0, :, 0]
                else:
                    # 输出与输入形状不匹配，返回错误
                    return {
                        "status": "error",
                        "error_type": "shape_mismatch",
                        "message": "模型输出形状与输入数据不匹配",
                        "details": {
                            "input_shape": str(eeg_data.shape),
                            "output_shape": str(model_output.shape),
                            "expected_channels": len(channel_names),
                            "data_file": data_file['original_filename'],
                            "model_file": model_file['original_filename'],
                            "original_data": {
                                "channels": channel_names,
                                "shape": list(eeg_data.shape),
                                "sample": original_sample[:5] if len(original_sample) > 5 else original_sample
                            }
                        }
                    }
        elif len(model_output.shape) == 2:
            if model_output.shape == eeg_data.shape:
                # 直接匹配
                processed_eeg_data = model_output
            elif model_output.shape[0] == eeg_data.shape[1] and model_output.shape[1] == eeg_data.shape[0]:
                # 时间点×通道 格式
                processed_eeg_data = model_output.T
            elif is_cnn_model and model_output.shape[0] == 1:
                # CNN模型可能输出(1, time_steps)
                # 尝试复制到多通道
                print(f"CNN模型输出扁平化结果，将复制到所有通道")
                processed_eeg_data = np.zeros((len(channel_names), model_output.shape[1]))
                for i in range(len(channel_names)):
                    processed_eeg_data[i, :] = model_output[0, :]
            elif model_output.shape[0] == 1 and model_output.shape[1] == eeg_data.shape[1]:
                # 单通道输出匹配时间维度
                print(f"扩展单通道输出到所有{len(channel_names)}个通道")
                processed_eeg_data = np.zeros((len(channel_names), eeg_data.shape[1]))
                for i in range(len(channel_names)):
                    processed_eeg_data[i, :] = model_output[0, :]
            else:
                # 输出与输入形状不匹配，返回错误
                return {
                    "status": "error",
                    "error_type": "shape_mismatch",
                    "message": "模型输出形状与输入数据不匹配",
                    "details": {
                        "input_shape": str(eeg_data.shape),
                        "output_shape": str(model_output.shape),
                        "data_file": data_file['original_filename'],
                        "model_file": model_file['original_filename'],
                        "original_data": {
                            "channels": channel_names,
                            "shape": list(eeg_data.shape),
                            "sample": original_sample[:5] if len(original_sample) > 5 else original_sample
                        }
                    }
                }
        # 添加专门处理CNN输出结果的情况
        elif is_cnn_model and len(model_output.shape) == 1:
            # 处理一维输出的情况
            print(f"处理CNN模型一维输出，形状: {model_output.shape}")
            # 检查时间维度是否匹配
            if model_output.shape[0] == eeg_data.shape[1]:
                # 时间维度匹配，复制到所有通道
                processed_eeg_data = np.zeros((len(channel_names), eeg_data.shape[1]))
                for i in range(len(channel_names)):
                    processed_eeg_data[i, :] = model_output
                print(f"已将一维输出扩展到所有通道，新形状: {processed_eeg_data.shape}")
            else:
                # 尝试调整大小
                min_length = min(model_output.shape[0], eeg_data.shape[1])
                processed_eeg_data = np.zeros((len(channel_names), eeg_data.shape[1]))
                # 填充可用部分
                for i in range(len(channel_names)):
                    processed_eeg_data[i, :min_length] = model_output[:min_length]
                print(f"已将一维输出调整并扩展到所有通道，新形状: {processed_eeg_data.shape}")
        else:
            # 输出与输入形状不匹配，返回错误
            return {
                "status": "error",
                "error_type": "shape_mismatch",
                "message": "模型输出形状与EEG数据不兼容",
                "details": {
                    "input_shape": str(eeg_data.shape),
                    "output_shape": str(model_output.shape),
                    "data_file": data_file['original_filename'],
                    "model_file": model_file['original_filename'],
                    "original_data": {
                        "channels": channel_names,
                        "shape": list(eeg_data.shape),
                        "sample": original_sample[:5] if len(original_sample) > 5 else original_sample
                    }
                }
            }
        
        return processed_eeg_data
    
    def _calculate_metrics(self, eeg_data, processed_eeg_data, channel_names, sampling_rate, 
                          original_sample, start_time, data_file, model_file):
        """
        计算评估指标
        
        Args:
            eeg_data: 原始EEG数据
            processed_eeg_data: 处理后的EEG数据
            channel_names: 通道名称
            sampling_rate: 采样率
            original_sample: 原始数据样本
            start_time: 开始时间
            data_file: 数据文件信息
            model_file: 模型文件信息
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        # 计算评估指标
        end_time = time.time()
        elapsed_time = (end_time - start_time)  # 秒
        
        # 计算各种评估指标
        mse = np.mean((eeg_data - processed_eeg_data) ** 2)
        mae = np.mean(np.abs(eeg_data - processed_eeg_data))
        
        # 计算SNR
        signal_power = np.mean(eeg_data ** 2)
        noise_power = np.mean((eeg_data - processed_eeg_data) ** 2)
        snr = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 100
        
        # 计算相关系数
        correlation = np.zeros(eeg_data.shape[0])
        for i in range(eeg_data.shape[0]):
            correlation[i] = np.corrcoef(eeg_data[i, :], processed_eeg_data[i, :])[0, 1]
        pearson = np.mean(correlation)
        
        # 创建处理后数据的样本（用于可视化）
        processed_sample = processed_eeg_data[:, :min(1000, processed_eeg_data.shape[1])].tolist()
        
        # 波形保真度（作为相似度的百分比）
        waveform_fidelity = (1 - np.sqrt(mse) / np.max(np.abs(eeg_data))) * 100
        
        # 返回结果
        return {
            "status": "success",
            "message": "模型评估成功",
            "data_file": data_file['original_filename'],
            "model_file": model_file['original_filename'],
            "visualization_data": {
                "original": {
                    "data": original_sample,
                    "channels": channel_names,
                    "sampling_rate": sampling_rate
                },
                "processed": {
                    "data": processed_sample,
                    "channels": channel_names,
                    "sampling_rate": sampling_rate
                }
            },
            "results": {
                "mse": float(mse),
                "mae": float(mae),
                "snr": float(snr),
                "pearson": float(pearson),
                "waveform_fidelity": float(waveform_fidelity),
                "elapsed_time": float(elapsed_time)
            }
        }
