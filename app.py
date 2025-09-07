from database import Base
from fastapi import FastAPI


app = FastAPI(title="Async FastAPI")


@app.on_event("startup")
async def startup():
    await Base.connect()


@app.on_event("shutdown")
async def shutdown():
    await Base.disconnect()



