from typing import Annotated

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.elasticsearch import get_es

DBSession = Annotated[AsyncSession, Depends(get_db)]
ESClient = Annotated[AsyncElasticsearch, Depends(get_es)]
