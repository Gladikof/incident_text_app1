"""
ML Scheduler - періодично перевіряє чи потрібно перенавчувати ML модель.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from app.database import SessionLocal
from app.services.active_learning_service import active_learning_service


class MLScheduler:
    """
    Background scheduler для автоматичного перенавчання ML моделі.
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False

    def check_and_retrain(self):
        """
        Periodic task що перевіряє чи потрібно перенавчувати модель.
        Запускається автоматично кожні 6 годин.
        """
        print(f"[MLScheduler] Running periodic retrain check at {datetime.utcnow()}")

        db = SessionLocal()
        try:
            job = active_learning_service.auto_retrain_if_needed(db)

            if job:
                print(
                    f"[MLScheduler] Retraining completed! Job ID: {job.id}, Status: {job.status}"
                )
            else:
                print(f"[MLScheduler] No retraining needed")

        except Exception as e:
            print(f"[MLScheduler] Error during retrain check: {e}")
        finally:
            db.close()

    def start(self):
        """
        Запускає scheduler.
        Перевірка відбувається кожні 6 годин.
        """
        if self.is_running:
            print("[MLScheduler] Already running")
            return

        # Додаємо periodic task
        self.scheduler.add_job(
            func=self.check_and_retrain,
            trigger=IntervalTrigger(hours=6),
            id="ml_retrain_check",
            name="Check if ML model needs retraining",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True
        print("[MLScheduler] Started - will check for retraining every 6 hours")

    def stop(self):
        """
        Зупиняє scheduler.
        """
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("[MLScheduler] Stopped")

    def trigger_immediate_check(self):
        """
        Запускає перевірку одразу (не чекаючи на scheduled time).
        Корисно для manual trigger з API.
        """
        print("[MLScheduler] Triggering immediate retrain check...")
        self.check_and_retrain()


# Глобальний інстанс
ml_scheduler = MLScheduler()
