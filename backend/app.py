# requires: fastapi==0.104.1
# requires: uvicorn[standard]==0.24.0
"""
FastAPI 应用入口
配置 CORS、注册路由、提供静态文件服务
"""
import sys
import os

# Windows 旧版本默认文件系统编码为 GBK，强制使用 UTF-8 避免中文路径乱码
if sys.platform == "win32":
    os.environ.setdefault("PYTHONUTF8", "1")
    if sys.flags.utf8_mode == 0:
        import warnings
        warnings.warn("建议以 PYTHONUTF8=1 启动，或使用 Python 3.7+ 并设置 UTF-8 模式，避免中文路径问题")

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

from api_routes import router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="技能管理工具 API",
    description="技能管理工具的后端 API",
    version="1.0.0"
)

# 配置 CORS（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(router)

# 静态文件目录
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# 挂载静态文件（CSS、JS等），直接挂载到根路径以匹配 index.html 中的相对路径引用
if FRONTEND_DIR.exists():
    logger.info(f"静态文件目录: {FRONTEND_DIR}")


@app.get("/")
async def root():
    """根路径，返回前端页面"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "技能管理工具 API", "docs": "/docs", "api": "/api"}


@app.get("/styles.css")
async def styles():
    """返回前端样式文件"""
    return FileResponse(FRONTEND_DIR / "styles.css", media_type="text/css")


@app.get("/app.js")
async def app_js():
    """返回前端 JS 文件"""
    return FileResponse(FRONTEND_DIR / "app.js", media_type="application/javascript")


@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {
        "status": "ok",
        "message": "技能管理工具运行正常"
    }


@app.on_event("startup")
async def startup_event():
    """
    应用启动时执行：自动扫描预设工具目录并写入配置
    """
    logger.info("技能管理工具启动")
    logger.info(f"API 文档: http://localhost:8000/docs")
    logger.info(f"前端页面: http://localhost:8000/")

    # 启动时扫描预设工具目录，新发现的自动写入配置
    try:
        from api_routes import config_manager
        newly_added = config_manager.apply_preset_scan()
        if newly_added:
            names = ", ".join(t.name for t in newly_added)
            logger.info(f"自动添加工具: {names}")
        else:
            logger.info("预设扫描：无新工具")
    except Exception as e:
        logger.warning(f"预设扫描失败（不影响启动）: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭时执行
    """
    logger.info("技能管理工具关闭")


def main():
    """
    主函数，启动 uvicorn 服务器
    """
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式，代码修改自动重载
        log_level="info"
    )


if __name__ == "__main__":
    main()
