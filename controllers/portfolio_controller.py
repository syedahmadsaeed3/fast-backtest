from cruds import portfolio_crud as crud
from database import get_supabase
from fastapi import Depends, HTTPException
from schemas import portfolio_schema as schema
from fastapi import APIRouter

router = APIRouter()


@router.post("/create_portfolio/")
def create_portfolio(data: schema.Portfolio, db=Depends(get_supabase)):
    try:

        portfolio_list = crud.get_all_portfolios(db, 1)
        exists = any(test.portfolio_name == data.portfolio_name for test in portfolio_list)
        if exists:
            raise Exception("portfolio_name already exists")
        else:
            crud.create_portfolio(db, data, 1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error: {e}")
    return {"message": "portfolio saved successfully"}


@router.get("/get_portfolios/")
def get_user_portfolios(db=Depends(get_supabase)):
    portfolio_list = crud.get_all_portfolios(db, 1)

    return {"results": portfolio_list}


@router.delete("/delete_portfolio/{portfolio_name}")
def delete_portfolio(portfolio_name: str, db=Depends(get_supabase)):
    try:
        portfolio_list = crud.get_all_portfolios(db, 1)
        exists = any(test.portfolio_name == portfolio_name for test in portfolio_list)
        if exists:
            crud.delete_portfolio(db, 1, portfolio_name)
            return {"message": "portfolio deleted successfully"}
        else:
            raise Exception("portfolio_name does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error: {e}")


@router.put("/update_portfolio/{portfolio_name}")
def update_portfolio(portfolio_name: str, data: schema.Portfolio, db=Depends(get_supabase)):
    try:
        portfolio_list = crud.get_all_portfolios(db, 1)
        exists = any(test.portfolio_name == portfolio_name for test in portfolio_list)
        if exists:
            test = crud.update_existing_portfolio(db, 1, data, portfolio_name)
            return {"message": test}
        else:
            raise {"message": "portfolio_name does not exist"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error: {e}")
