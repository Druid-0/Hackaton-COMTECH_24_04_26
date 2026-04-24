from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class ApplicationRecord(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    age: Mapped[float] = mapped_column(Float)
    monthly_income: Mapped[float] = mapped_column(Float)
    employment_years: Mapped[float] = mapped_column(Float)
    loan_amount: Mapped[float] = mapped_column(Float)
    loan_term_months: Mapped[float] = mapped_column(Float)
    interest_rate: Mapped[float] = mapped_column(Float)
    past_due_30d: Mapped[float] = mapped_column(Float)
    inquiries_6m: Mapped[float] = mapped_column(Float)

    p_default: Mapped[float] = mapped_column(Float)
    p_non_default: Mapped[float] = mapped_column(Float)
    label: Mapped[str] = mapped_column(String(32))
    threshold: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(64), default="v1_optimized")
