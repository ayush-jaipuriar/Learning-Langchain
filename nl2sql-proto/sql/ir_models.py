from typing import List, Optional, Literal

from pydantic import BaseModel
from pydantic import ConfigDict


class Projection(BaseModel):
    expr: str
    alias: Optional[str] = None


class Filter(BaseModel):
    expr: str


class OrderBy(BaseModel):
    expr: str
    direction: Literal["ASC", "DESC"] = "ASC"


class IR(BaseModel):
    table: str
    projections: List[Projection]
    filters: List[Filter] = []
    group_by: List[str] = []
    order_by: List[OrderBy] = []
    limit: Optional[int] = None
    dialect: Literal["duckdb"] = "duckdb"

    model_config = ConfigDict(extra="forbid")

