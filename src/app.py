import sys
import logging
from pathlib import Path

# Đảm bảo Windows console và logging luôn hỗ trợ UTF-8 không bao giờ bị lỗi charmap cp1252
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from src.api.routes import router
from src.database.connection import init_db
from src.config.settings import LotteryType, settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

SRC_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Vietlott Analytics",
    description="Statistical analysis and prediction engine for Vietlott lottery. Model scores are NOT mathematical probabilities.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = SRC_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates
templates = Jinja2Templates(directory=str(SRC_DIR / "templates"))

# Automatically initialize DB tables on startup
init_db()

import asyncio

async def scheduled_fetch_worker():
    """
    Tiến trình chạy ngầm tự động:
    - Chờ 10 giây sau khi mở app để nhường tài nguyên cho giao diện hiển thị ngay lập tức.
    - Định kỳ mỗi giờ kiểm tra 1 lần để kịp thời bắt các kỳ quay mới sau giờ mở thưởng (18h15 - 18h30).
    """
    await asyncio.sleep(10)
    while True:
        try:
            from src.database.connection import SessionLocal
            from src.api.service import AnalyticsService
            with SessionLocal() as db:
                service = AnalyticsService(db)
                for lt in [LotteryType.MEGA_645, LotteryType.POWER_655]:
                    res = service.fetch_data(lt, limit=100)
                    added = res.get("records_added", 0)
                    if added > 0:
                        logger.info(f"Cap nhat ky moi cho {lt.value}: +{added} ky")
        except Exception as e:
            logger.error(f"Loi kiem tra ky moi tu dong: {e}")
        # Kiểm tra lại sau mỗi 1 giờ (3600 giây)
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup():
    init_db()
    asyncio.create_task(scheduled_fetch_worker())
    logger.info("Vietlott Analytics started with automated background scheduler.")

# Include API routes
app.include_router(router)

# Frontend routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "lottery_type": "MEGA_645",
            "lottery_types": [{"value": lt.value, "label": "Mega 6/45" if lt == LotteryType.MEGA_645 else "Power 6/55"} for lt in LotteryType]
        }
    )

@app.get("/dashboard/{lottery_type}", response_class=HTMLResponse)
async def dashboard(request: Request, lottery_type: str):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "lottery_type": lottery_type,
            "lottery_types": [{"value": lt.value, "label": "Mega 6/45" if lt == LotteryType.MEGA_645 else "Power 6/55"} for lt in LotteryType]
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
