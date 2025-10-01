from flask_sqlalchemy import SQLAlchemy, query
from typing import Optional, TypeVar, Type, List

T = TypeVar('T')

class BaseRepository:
    model: Type[T] = None
    order_by: tuple = None
    
    def __init__(self, db_connector: SQLAlchemy):
        self.db_connector = db_connector

    def _get_all_query(self, order_by = None, query = None, **kwargs) -> query:
        if query is None:
            query = self.db_connector.select(self.model).filter_by(**kwargs)
            if order_by:
                query = query.order_by(*order_by)
        return query

    def _get_one(self, **kwargs) -> Optional[T]:
        return self.db_connector.session.execute(self._get_all_query(order_by=None, **kwargs)).scalar_one_or_none()

    def _get_all(self, order_by = None, **kwargs) -> List[Optional[T]]:
        return self.db_connector.session.execute(self._get_all_query(order_by=order_by, **kwargs)).scalars().all()

    def rollback(self) -> None:
        self.db_connector.session.rollback()
