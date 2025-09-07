import json
from fastapi.responses import JSONResponse
from controllers.auth_manager import JWTBearer
from schemas import user_schema as schemas
from typing import List
from database import get_supabase
from fastapi import Depends
from fastapi import APIRouter

from schemas.user_schema import SlackToken

router = APIRouter()


@router.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db=Depends(get_supabase)):
    db.auth.admin.create_user(email=user.email, password=user.password, first_name=user.first_name, last_name=user.last_name)


@router.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db=Depends(get_supabase)):
    pass


@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db=Depends(get_supabase)):
    pass


@router.post("/user/update_slack_token")
def update_slack_token(slack_token: SlackToken, db=Depends(get_supabase), user=Depends(JWTBearer())):
    try:
        db.table('users').update(json.loads(slack_token.json()))\
            .eq('id', user.id).execute()
        return JSONResponse(content="update completed")
    except Exception as e:
        return JSONResponse(content=f"error occurred while updating token: {e}")
