

from sqlalchemy.orm import Session
from src.app.models import dbmodels






def enqueue_email(to_email: str, subject: str, html_body: str, db: Session):
    payload={
        "to_email": to_email,
        "subject": subject,
        "html_body": html_body
    }

    job = dbmodels.Job(
        type="send_email",
        payload=payload
    )

    db.add(job)
    db.commit()
    db.refresh(job)
    return {"status": "Email sent!"}
