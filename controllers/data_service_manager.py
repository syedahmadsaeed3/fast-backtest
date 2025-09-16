from services.polygon_service import PolygonService
from services.yfinance_service import Yfinance
from settings import DATA_SERVICE


def get_data_service():
    if DATA_SERVICE == 0:
        return Yfinance()
    elif DATA_SERVICE == 1:
        return PolygonService()
