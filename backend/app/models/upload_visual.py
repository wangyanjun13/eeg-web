from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class FileMetadata(BaseModel):
    """文件元数据模型"""
    id: str
    name: str
    description: Optional[str] = None
    original_filename: str
    saved_filename: str
    file_type: str  # "data" 或 "model"
    file_format: str  # "set", "fdt", "mat", "npy" 或 "h5"
    upload_time: str
    file_size: int
    file_path: str

class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    status: str
    message: str
    file_id: str
    metadata: FileMetadata

class FileListResponse(BaseModel):
    """文件列表响应模型"""
    status: str
    files: List[FileMetadata]

class FileDetailResponse(BaseModel):
    """文件详情响应模型"""
    status: str
    file: FileMetadata

class FileDeleteResponse(BaseModel):
    """文件删除响应模型"""
    status: str
    message: str
