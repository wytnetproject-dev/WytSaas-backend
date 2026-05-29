from typing import Optional, List, Generic, TypeVar, Any, Union
from pydantic import BaseModel

T = TypeVar('T')

class Pagination(BaseModel):
    next_cursor: Optional[str] = None
    total: int
    page: int
    size: int
    pages: int

class APIResponse(BaseModel, Generic[T]):
    items: Optional[List[T]] = None
    item: Optional[T] = None
    id : Optional[Union[int, str]] = None
    detail: Optional[str] = ""
    itemCount : Optional[Any] = None

    pagination: Optional[Pagination] = None