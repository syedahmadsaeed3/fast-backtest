from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers import backtest_controller, ticker_controller, portfolio_controller, user_controller


web_app = FastAPI()

web_app.include_router(backtest_controller.router)
web_app.include_router(ticker_controller.router)
web_app.include_router(portfolio_controller.router)
web_app.include_router(user_controller.router)

origins = ["http://localhost", "http://localhost:8080", "http://127.0.0.1", "http://127.0.0.1:8080",
           "http://localhost:3000", "http://127.0.0.1:3000", "https://stagingauth.eagletrend.net"]
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


