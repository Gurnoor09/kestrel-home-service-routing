"""Pydantic schemas for Kestrel routing API."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ServiceRequestInput(BaseModel):
    request_text: str = Field(..., description="Customer initial message or IVR transcript")
    product_family: str = Field(..., description="Product category, e.g., Water Purifier, Air Fryer")
    warranty_status: str = Field(..., description="Warranty tier: in_warranty, shield, out_of_warranty")
    channel: str = Field(..., description="Intake channel: chat, whatsapp, ivr, email")
    request_id: Optional[str] = Field(None, description="Optional request identifier")


class RoutingPredictionResponse(BaseModel):
    request_id: Optional[str] = None
    predicted_team: str
    confidence: float
    reasons: List[str]
    model_signal: str
    probabilities: dict
