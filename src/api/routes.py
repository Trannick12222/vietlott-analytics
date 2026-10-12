from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from src.config.settings import LotteryType
from src.database.connection import get_db
from src.api.service import AnalyticsService
from src.api.schemas import DrawResponse, FetchRequest, CustomPoolRequest, SuitabilityRequest

router = APIRouter(prefix="/api", tags=["api"])

def get_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "Vietlott Analytics API is running"}

@router.get("/draws/{lottery_type}")
def get_draws(
    lottery_type: LotteryType,
    limit: int = Query(100, ge=1, le=1000),
    service: AnalyticsService = Depends(get_service)
):
    try:
        return service.get_latest_draws(lottery_type, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/{lottery_type}")
def get_statistics(
    lottery_type: LotteryType,
    service: AnalyticsService = Depends(get_service)
):
    result = service.get_statistics(lottery_type)
    if not result:
        raise HTTPException(status_code=404, detail="No data available. Fetch data first.")
    return result

@router.get("/predictions/{lottery_type}")
def get_predictions(
    lottery_type: LotteryType,
    threshold: float = Query(50.0, ge=0, le=100),
    service: AnalyticsService = Depends(get_service)
):
    result = service.get_predictions(lottery_type, threshold)
    if not result:
        raise HTTPException(status_code=404, detail="No data available. Fetch data first.")
    return result

@router.get("/combinations/bao/{lottery_type}")
def get_bao_combinations(
    lottery_type: LotteryType,
    bao_type: int = Query(7, ge=5, le=18),
    service: AnalyticsService = Depends(get_service)
):
    result = service.get_bao_combinations(lottery_type, bao_type)
    if not result:
        raise HTTPException(status_code=404, detail="No data available. Fetch data first.")
    return result

@router.get("/combinations/wheeling/{lottery_type}")
def get_wheeling_combinations(
    lottery_type: LotteryType,
    wheel_size: int = Query(12, ge=10, le=14),
    strategy: str = Query("balanced"),
    service: AnalyticsService = Depends(get_service)
):
    result = service.get_wheeling_combinations(lottery_type, wheel_size, strategy=strategy)
    if not result:
        raise HTTPException(status_code=404, detail="No data available. Fetch data first.")
    return result

@router.post("/combinations/custom")
def optimize_custom_combinations(
    req: CustomPoolRequest,
    service: AnalyticsService = Depends(get_service)
):
    try:
        result = service.optimize_custom_pool(req.lottery_type, req.numbers, req.ticket_count)
        if not result:
            raise HTTPException(status_code=404, detail="No data available. Fetch data first.")
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/combinations/evaluate-suitability")
def evaluate_suitability(
    req: SuitabilityRequest,
    service: AnalyticsService = Depends(get_service)
):
    try:
        return service.evaluate_pool_suitability(req.numbers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/backtest/{lottery_type}")
def get_backtest(
    lottery_type: LotteryType,
    service: AnalyticsService = Depends(get_service)
):
    return service.get_backtest_results(lottery_type)

@router.post("/fetch")
def fetch_data(
    req: FetchRequest,
    service: AnalyticsService = Depends(get_service)
):
    try:
        return service.fetch_data(req.lottery_type, req.limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/{lottery_type}")
def get_dashboard(
    lottery_type: LotteryType,
    service: AnalyticsService = Depends(get_service)
):
    try:
        return service.get_dashboard_data(lottery_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
