from pydantic import BaseModel
from typing import Optional, Any, List


class Pagination(BaseModel):
    start: Optional[int] = None
    end: Optional[int] = None
    count: int
    data: List[Any]




