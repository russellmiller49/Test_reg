from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProcedureType(str, Enum):
    EBUS = "EBUS"
    NAVIGATIONAL = "NAVIGATIONAL"
    ROBOTIC = "ROBOTIC"
    THERAPEUTIC = "THERAPEUTIC"


class AnnotationBase(BaseModel):
    date: date
    operators: Optional[List[str]] = None
    sedation: Optional[str] = None
    complications: Optional[str] = None
    notes: Optional[str] = None


class AnnotationCreate(AnnotationBase):
    procedure_type: ProcedureType
    procedure_details: Dict[str, Any] = Field(default_factory=dict)


class AnnotationRead(AnnotationBase):
    id: int
    procedure_type: ProcedureType
    procedure_details: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}
