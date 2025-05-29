from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from ..models.openapi_doc import OpenAPIDoc


def create_openapi_doc(db: Session, project_id: int, task_id: int, openapi_spec: Dict[str, Any]) -> OpenAPIDoc:
    db_doc = OpenAPIDoc(
        project_id=project_id,
        task_id=task_id,
        openapi_spec=openapi_spec
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def get_latest_openapi_doc_by_project_id(db: Session, project_id: int) -> Optional[OpenAPIDoc]:
    return db.query(OpenAPIDoc).filter(OpenAPIDoc.project_id == project_id).order_by(OpenAPIDoc.created_at.desc()).first()

def get_openapi_doc_by_task_id(db: Session, task_id: int) -> Optional[OpenAPIDoc]:
    return db.query(OpenAPIDoc).filter(OpenAPIDoc.task_id == task_id).first()
