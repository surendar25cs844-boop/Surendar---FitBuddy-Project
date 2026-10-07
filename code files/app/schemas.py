from typing import Literal

from pydantic import BaseModel, Field


Goal = Literal[
    "weight_loss",
    "muscle_gain",
    "general_wellness",
    "flexibility",
]

Intensity = Literal["low", "medium", "high"]


class UserInput(BaseModel):
    user_key: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=16, le=100)
    weight_kg: float = Field(gt=25, le=350)
    goal: Goal
    intensity: Intensity


class FeedbackRequest(BaseModel):
    user_key: str = Field(min_length=2, max_length=80)
    feedback: str = Field(min_length=3, max_length=1000)


class GenerateResponse(BaseModel):
    user_key: str
    workout_plan: str
    nutrition_tip: str
    ai_mode: str


class FeedbackResponse(BaseModel):
    user_key: str
    workout_plan: str
    nutrition_tip: str
    ai_mode: str