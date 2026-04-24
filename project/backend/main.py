from pathlib import Path

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from model_service import OptimizedLogReg
from models import ApplicationRecord
from schemas import CreditApplication, PredictResponse

app = FastAPI(title="Credit Scoring API", version="2.0.0")

data_file = (
    Path(__file__).resolve().parents[2]
    / "Hackaton"
    / "data"
    / "credit_scoring_dataset.csv"
)

model = OptimizedLogReg(data_file)

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "model_version": model.model_version}


@app.get("/metrics")
def get_metrics():
    return model.metrics


@app.post("/predict", response_model=PredictResponse)
def predict(application: CreditApplication, db: Session = Depends(get_db)):
    payload = application.model_dump()
    p_default, label = model.predict(payload)
    p_non_default = 1 - p_default

    record = ApplicationRecord(
        **payload,
        p_default=p_default,
        p_non_default=p_non_default,
        label=label,
        threshold=model.threshold,
        model_version=model.model_version,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "label": label,
        "p_default": round(p_default, 4),
        "p_non_default": round(p_non_default, 4),
        "threshold": model.threshold,
        "model_version": model.model_version,
        "metrics": model.metrics,
    }


@app.get("/applications")
def list_applications(limit: int = 20, db: Session = Depends(get_db)):
    rows = (
        db.query(ApplicationRecord)
        .order_by(ApplicationRecord.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "age": r.age,
            "monthly_income": r.monthly_income,
            "employment_years": r.employment_years,
            "loan_amount": r.loan_amount,
            "loan_term_months": r.loan_term_months,
            "interest_rate": r.interest_rate,
            "past_due_30d": r.past_due_30d,
            "inquiries_6m": r.inquiries_6m,
            "p_default": round(r.p_default, 4),
            "p_non_default": round(r.p_non_default, 4),
            "label": r.label,
            "threshold": r.threshold,
            "model_version": r.model_version,
        }
        for r in rows
    ]
