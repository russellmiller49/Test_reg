from fastapi import APIRouter

from .annotations import router as annotations_router

router = APIRouter()
router.include_router(annotations_router)

__all__ = ["router"]
