from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...crud import crud_openapi_doc

router = APIRouter()

@router.get("/{project_id}")
def read_latest_openapi_document(
    project_id: int,
    db: Session = Depends(get_db)
):
    latest_doc = crud_openapi_doc.get_latest_openapi_doc_by_project_id(db, project_id=project_id)
    
    if latest_doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No OpenAPI document found for this project.")
    
    return latest_doc.openapi_spec
