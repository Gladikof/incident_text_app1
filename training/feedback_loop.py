"""Utility script to rebuild training datasets from production feedback."""
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.training_feedback_service import training_feedback_service


@contextmanager
def session_scope():
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()


def main() -> None:
    with session_scope() as session:
        path = training_feedback_service.export_priority_feedback_dataset(session)
        print(f"[training] Exported priority feedback dataset to {path}")


if __name__ == "__main__":
    main()
