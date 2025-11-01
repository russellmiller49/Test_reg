from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, Date, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from . import Base


class Annotation(Base):
    __tablename__ = "annotations"

    id: int = Column(Integer, primary_key=True, index=True)
    date: date = Column(Date, nullable=False)
    operators: Optional[List[str]] = Column(JSONB().with_variant(JSON, "sqlite"), nullable=True)
    sedation: Optional[str] = Column(Text, nullable=True)
    complications: Optional[str] = Column(Text, nullable=True)
    notes: Optional[str] = Column(Text, nullable=True)
    procedure_type: str = Column(Text, nullable=False, default="EBUS")
    procedure_details: Optional[Dict[str, Any]] = Column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=True,
    )
