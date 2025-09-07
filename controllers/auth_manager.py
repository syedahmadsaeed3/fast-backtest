from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from database import get_supabase
from cruds.user_crud import get_user


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request, db=Depends(get_supabase)):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme")
            try:
                data = get_user(db, credentials.credentials)
                return data.user
            except Exception:
                raise HTTPException(status_code=403, detail="Invalid authorization code or user does not exist")
        else:
            raise HTTPException(status_code=401, detail="User not authenticated")
