from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.annotation import Annotation
from app.schemas.annotation import AnnotationCreate, AnnotationRead, ProcedureType

router = APIRouter(prefix="/annotations", tags=["annotations"])


def _to_read_model(entity: Annotation) -> AnnotationRead:
    operators = entity.operators if entity.operators is not None else None
    return AnnotationRead(
        id=entity.id,
        date=entity.date,
        operators=operators,
        sedation=entity.sedation,
        complications=entity.complications,
        notes=entity.notes,
        procedure_type=ProcedureType(entity.procedure_type),
        procedure_details=entity.procedure_details or {},
    )


@router.post("", response_model=AnnotationRead, status_code=status.HTTP_201_CREATED)
def create_annotation(payload: AnnotationCreate, db: Session = Depends(get_db)) -> AnnotationRead:
    annotation = Annotation(
        date=payload.date,
        operators=payload.operators,
        sedation=payload.sedation,
        complications=payload.complications,
        notes=payload.notes,
        procedure_type=payload.procedure_type.value,
        procedure_details=payload.procedure_details,
    )
    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    return _to_read_model(annotation)


@router.get("", response_model=List[AnnotationRead])
def list_annotations(db: Session = Depends(get_db)) -> List[AnnotationRead]:
    records = db.query(Annotation).order_by(Annotation.id.desc()).all()
    return [_to_read_model(record) for record in records]


@router.get("/{annotation_id}", response_model=AnnotationRead)
def get_annotation(annotation_id: int, db: Session = Depends(get_db)) -> AnnotationRead:
    annotation = db.get(Annotation, annotation_id)
    if annotation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found")
    return _to_read_model(annotation)
