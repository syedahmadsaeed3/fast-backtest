from typing import List
from cruds import ticker_crud as crud
from database import get_supabase
from fastapi import Depends
from schemas import ticker_schema as schema
from schemas.pagination import Pagination
from services.binance_service import BinanceService
from services.polygon_service import PolygonService
from fastapi import APIRouter

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


@router.post("/get_tickers/", response_model=Pagination)
def get_tickers(db=Depends(get_supabase)):
    tickers = crud.get_all_tickers(db)
    return tickers


@router.post("/get_ticker/{symbol}", response_model=schema.Ticker)
def get_ticker(symbol: str, db=Depends(get_supabase)):
    tickers = crud.get_ticker(db, symbol)
    return tickers


@router.post("/search_ticker/{query}", response_model=List[schema.Ticker])
def search_ticker(query: str, db=Depends(get_supabase)):
    tickers = crud.search_ticker(db, query)
    return tickers
