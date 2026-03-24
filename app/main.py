"""FastAPI应用入口"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from app.api.endpoints import router as api_router
from app.api.monitoring import router as monitoring_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    from app.database import init_db
    from app.database.vector_init import init_vector_store

    # 初始化 SQLite 数据库
    init_db()
    logger.info("SQLite 数据库已初始化")

    # 初始化向量数据库（如果为空则自动初始化）
    await init_vector_store()

    yield
    logger.info("服务已关闭")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description="基于RAG和Agent的电商管理客服系统",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有域名访问（生产环境应指定具体域名）
    allow_credentials=True,  # 允许携带 Cookie、Authorization header 等认证信息
    allow_methods=["*"],  # 允许所有 HTTP 方法（GET、POST、PUT、DELETE 等）
    allow_headers=["*"],  # 允许所有 HTTP 头（Content-Type、Authorization 等）
)

# 中间件
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# 注册异常处理器
register_exception_handlers(app)

# 路由
app.include_router(api_router, prefix="/api", tags=["聊天"])
app.include_router(monitoring_router, tags=["监控"])


@app.get("/")
async def root():
    return {"message": "欢迎使用电商管理客服系统", "app": settings.app_name}