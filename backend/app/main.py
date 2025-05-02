from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pathlib import Path

# 直接导入路由器
from app.api.dataset import router as dataset_router
from app.api.visualization import router as visual_router
from app.api.preprocess import router as preprocess_router
from app.api.analysis import router as analysis_router

# 导入Redis检查
from app.core.redis import check_redis_connection

app = FastAPI(
    title="EEG数据分析API",
    description="用于EEG数据处理和分析的后端API",
    version="1.0.0",
    # 禁用尾部斜杠重定向
    redirect_slashes=False
)

# 自定义OpenAPI文档
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="EEG数据分析平台API",
        version="1.0.0",
        description="EEG数据分析平台的API文档",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    # 允许所有前端开发环境的源
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],  # 添加通配符
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(dataset_router)
app.include_router(visual_router)
app.include_router(preprocess_router)
app.include_router(analysis_router)

@app.get("/")
async def root():
    return {"message": "EEG分析平台API正在运行"}

@app.get("/health")
async def health_check():
    # 检查Redis连接状态
    redis_status = "connected" if check_redis_connection() else "disconnected"
    return {
        "status": "healthy", 
        "redis": redis_status
    }

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    # 启动时检查Redis连接
    if check_redis_connection():
        print("✅ Redis连接成功")
    else:
        print("⚠️ Redis连接失败，将使用内存缓存")