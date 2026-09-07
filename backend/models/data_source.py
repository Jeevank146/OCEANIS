from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.data_refresh_log import DataRefreshLog


class DataSource(Base, TimestampMixin):
    """
    Represents an external or internal data source feeding oceanographic,
    meteorological, or geospatial intelligence into OCEANIS.
    """
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    refresh_logs: Mapped[List["DataRefreshLog"]] = relationship(
        "DataRefreshLog",
        back_populates="data_source",
        cascade="all, delete-orphan",
        order_by="desc(DataRefreshLog.started_at)",
    )

    def __repr__(self) -> str:
        return f"<DataSource(id={self.id}, name='{self.name}', provider='{self.provider}', is_active={self.is_active})>"
