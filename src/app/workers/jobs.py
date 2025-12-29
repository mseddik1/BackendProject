import time
from sqlalchemy.orm import Session
from src.app.db import base
from src.app.models import dbmodels
from src.app.enums import enums
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.app.core.config import settings
import smtplib
import json





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




def process_send_email(job: dbmodels.Job):
    data = job.payload
    to_email = data["to_email"]
    subject = data["subject"]
    html_body = data["html_body"]
    # Create the MIME message
    message = MIMEMultipart()
    message["From"] = settings.SENDER_EMAIL
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(html_body, "html"))

    # Send via Gmail SMTP
    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
        server.starttls()  # Secure connection
        server.login(settings.SENDER_EMAIL, settings.APP_PASSWORD)
        server.sendmail(settings.SENDER_EMAIL, to_email, message.as_string())

        print(f"[WORKER] Sent an email to  {to_email} (job {job.id})")

    return {"status": "Email sent!"}

def mark_job_failed_with_retry(job: dbmodels.Job):
    job.attempts = (job.attempts or 0) + 1
    if job.attempts < (job.max_attempts or 3):
        time.sleep(2)
        job.status = "pending"
    else:
        job.status = "failed"

def worker_loop():
    while True:
        db: Session = base.SessionLocal()
        try:
            job = (
                db.query(dbmodels.Job)
                .filter(
                    dbmodels.Job.status == "pending"
                )
                .order_by(dbmodels.Job.created_at)
                .first()
            )

            if not job:
                time.sleep(2)  # sleep 2 seconds then check again
                continue

            job.status = "processing"
            db.commit()
            db.refresh(job)

            match job.type:
                case enums.JobType.PUBLISH_PRODUCT.value:
                    try:
                        process_publish_product_job(db, job)
                        job.status = "done"
                    except Exception as e:
                        print(f"[WORKER] Job {job.id} failed: {e}")
                        mark_job_failed_with_retry(job)

                case enums.JobType.SEND_EMAIL.value:
                    try:
                        process_send_email(job)
                        job.status = "done"
                    except Exception as e:
                        print(f"[WORKER] Job {job.id} failed: {e}")
                        mark_job_failed_with_retry(job)


            db.commit()
            db.refresh(job)

        finally:
            db.close()


if __name__ == "__main__":
    print("[WORKER] Starting publish_product worker...")
    worker_loop()