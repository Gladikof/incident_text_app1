"""
Початкове тренування ML моделі на seed даних.
Використовується після seed_tickets_fast.py для швидкого старту системи.
"""
from app.database import SessionLocal
from app.models.ticket import Ticket
from app.services.active_learning_service import active_learning_service
from app.core.enums import PriorityEnum


def train_initial_model():
    """
    Тренує початкову ML модель на існуючих тікетах.
    """
    db = SessionLocal()

    try:
        # Перевірити кількість тікетів
        total_tickets = db.query(Ticket).count()

        print("=" * 60)
        print("  Initial ML Model Training")
        print("=" * 60)
        print()
        print(f"Total tickets in database: {total_tickets}")

        if total_tickets < 50:
            print(f"WARNING: Only {total_tickets} tickets found.")
            print(f"Recommended minimum: 50 tickets")
            print(f"Run: python seed_tickets_fast.py 100")
            print()

        # Показати розподіл по пріоритетах
        print("Priority distribution:")
        for priority in PriorityEnum:
            count = db.query(Ticket).filter(Ticket.priority_manual == priority).count()
            if count > 0:
                print(f"  - {priority.value}: {count} ({count/total_tickets*100:.1f}%)")

        print("\nStarting training...\n")

        # Запустити тренування через active learning service
        job = active_learning_service.train_model(db, training_type="INITIAL")

        print(f"\nTraining completed!")
        print(f"Model version: {job.model_version}")
        print(f"Training samples: {job.total_training_samples}")
        print(f"Duration: {(job.completed_at - job.started_at).total_seconds():.1f}s")

        # Показати метрики якщо є
        from app.models.ml_model_metadata import MLModelMetadata
        model = db.query(MLModelMetadata).filter(
            MLModelMetadata.version == job.model_version
        ).first()

        if model and model.accuracy:
            print(f"\nModel Metrics:")
            print(f"  - Accuracy: {model.accuracy * 100:.2f}%")
            if model.f1_score:
                print(f"  - F1 Score: {model.f1_score * 100:.2f}%")
            if model.precision_p1:
                print(f"  - Precision P1: {model.precision_p1 * 100:.2f}%")
            if model.precision_p2:
                print(f"  - Precision P2: {model.precision_p2 * 100:.2f}%")
            if model.precision_p3:
                print(f"  - Precision P3: {model.precision_p3 * 100:.2f}%")

        print(f"\nModel is now active and ready to use!")
        print(f"View in dashboard: http://localhost:8000/ml-training.html")

    except Exception as e:
        print(f"\nERROR: Training failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    train_initial_model()
