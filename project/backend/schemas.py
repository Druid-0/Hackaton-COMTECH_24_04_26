from pydantic import BaseModel, Field


class CreditApplication(BaseModel):
    age: float = Field(..., ge=18)
    monthly_income: float = Field(..., ge=0)
    employment_years: float = Field(..., ge=0)
    loan_amount: float = Field(..., ge=0)
    loan_term_months: float = Field(..., ge=1)
    interest_rate: float = Field(..., ge=0)
    past_due_30d: float = Field(..., ge=0)
    inquiries_6m: float = Field(..., ge=0)


class PredictResponse(BaseModel):
    label: str
    p_default: float
    p_non_default: float
    threshold: float
    model_version: str
    metrics: dict
