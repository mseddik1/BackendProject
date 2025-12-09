import time
from sqlalchemy.orm import Session
from src.app.db import base
from src.app.models import dbmodels
from src.app.enums import enums



def process_publish_product_job(db: Session, job: dbmodels.Job):
    time.sleep(10)

    product_data = job.payload
    product_id = product_data["id"]

    product_db = (
        db.query(dbmodels.Products)
        .filter(dbmodels.Products.id == product_id)
        .first()
    )

    if not product_db:
        print(f"[WORKER] Product {product_id} not found for job {job.id}")
        return


    product_db.is_active = True
    db.commit()

    print(f"[WORKER] Published product {product_id} (job {job.id})")


def worker_loop():
    while True:
        db: Session = base.SessionLocal()
        try:
            job = (
                db.query(dbmodels.Job)
                .filter(
                    dbmodels.Job.status == "pending",
                    dbmodels.Job.type == enums.JobType.PUBLISH_PRODUCT.value,
                )
                .order_by(dbmodels.Job.created_at)
                .first()
            )

            if not job:
                db.close()
                time.sleep(2)  # sleep 2 seconds then check again
                continue

            job.status = "processing"
            db.commit()
            db.refresh(job)

            try:
                process_publish_product_job(db, job)
                job.status = "done"
            except Exception as e:
                print(f"[WORKER] Job {job.id} failed: {e}")
                job.status = "failed"

            db.commit()
        finally:
            db.close()


if __name__ == "__main__":
    print("[WORKER] Starting publish_product worker...")
    worker_loop()