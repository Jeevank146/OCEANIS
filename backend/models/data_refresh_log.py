from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.data_source import DataSource


class DataRefreshLog(Base):
    """
    Logs data ingestion, synchronization, and refresh runs for a DataSource.
    """
    __tablename__ = "data_refresh_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    data_source_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="STARTED",
    )
    records_processed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    data_source: Mapped["DataSource"] = relationship(
        "DataSource",
        back_populates="refresh_logs",
    )

    def __repr__(self) -> str:
        return f"<DataRefreshLog(id={self.id}, data_source_id={self.data_source_id}, status='{self.status}')>"
