from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Select, select

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    model: Optional[Type[ModelType]] = None
    default_order_by: Optional[Sequence[Any]] = None

    def __init__(self, db: SQLAlchemy) -> None:
        self._db = db

    @property
    def session(self):
        return self._db.session

    def _build_select(
        self,
        *,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[Sequence[Any]] = None,
    ) -> Select:
        if self.model is None:
            raise NotImplementedError("Repository model is not configured")

        stmt = select(self.model)

        if filters:
            stmt = stmt.filter_by(**filters)

        if order_by is None:
            order_by = self.default_order_by

        if order_by:
            stmt = stmt.order_by(*order_by)

        return stmt

    def _get_one(self, **filters: Any) -> Optional[ModelType]:
        stmt = self._build_select(filters=filters)
        return self.session.execute(stmt).scalar_one_or_none()

    def _get_all(
        self,
        *,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[Sequence[Any]] = None,
    ) -> list[ModelType]:
        stmt = self._build_select(filters=filters, order_by=order_by)
        result = self.session.execute(stmt)
        return list(result.scalars())

    def add(self, instance: ModelType) -> None:
        self.session.add(instance)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()


__all__ = ["BaseRepository"]
