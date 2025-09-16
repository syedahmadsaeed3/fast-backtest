from typing import List

from controllers.data_service_manager import get_data_service
from cruds import ticker_crud as crud
from database import get_supabase
from fastapi import Depends
from schemas import ticker_schema as schema
from schemas.pagination import Pagination
from services.binance_service import BinanceService
from services.polygon_service import PolygonService
from fastapi import APIRouter

from services.yfinance_service import Yfinance

router = APIRouter()


@router.post("/update_tickers/")
def update_tickers(db=Depends(get_supabase)):
    polygon = PolygonService()
    tickers = polygon.get_all_tickers_complete()
    crud.bulk_insert_ticker(db, tickers)
    return {"message": "tickers updated successfully"}


@router.post("/update_crypto/")
def update_crypto(db=Depends(get_supabase)):
    binance = BinanceService()
    crypto = binance.get_all_crypto()
    crud.bulk_insert_ticker(db, crypto)
    return {"message": "crypto updated successfully"}


@router.get("/get_tickers/", response_model=Pagination)
def get_tickers(db=Depends(get_supabase)):
    tickers = crud.get_all_tickers(db)
    return tickers


@router.get("/get_ticker/{symbol}", response_model=schema.Ticker)
def get_ticker(symbol: str, days: int = 100, db=Depends(get_supabase)):
    tickers = crud.get_ticker(db, symbol)
    try:
        data_service = get_data_service()
    except Exception as e:
        print(e)
        data_service = Yfinance()
    response = data_service.get_n_day_data(days, symbol)
    tickers['close'] = [x.close for x in response]
    tickers['timestamp'] = [x.timestamp for x in response]
    return tickers


@router.get("/search_ticker/{query}", response_model=List[schema.Ticker])
def search_ticker(query: str, db=Depends(get_supabase)):
    tickers = crud.search_ticker(db, query)
    return tickers

