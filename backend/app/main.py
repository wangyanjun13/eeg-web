from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pathlib import Path

# 直接导入路由器
from app.api.dataset import router as dataset_router
from app.api.visualization import router as visual_router
from app.api.preprocess import router as preprocess_router
from app.api.analysis import router as analysis_router

app = FastAPI(
    title="EEG Analyzer",
    description="EEG数据分析平台",
    version="1.0.0"
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
    allow_origins=["http://localhost:5173"],
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
    return {"status": "healthy"}