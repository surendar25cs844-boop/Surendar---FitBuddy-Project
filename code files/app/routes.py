from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import ai, models
from app.database import get_db
from app.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    GenerateResponse,
    UserInput,
)
from app.services import all_users, get_user_with_plan, save_user_and_plan


router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent / "templates"
)


def result_context(request, user, plan, ai_mode):
    return {
        "request": request,
        "user": user,
        "plan": plan,
        "ai_mode": ai_mode,
    }


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"error": None},
    )


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_form(
    request: Request,
    user_key: str = Form(...),
    name: str = Form(...),
    age: int = Form(...),
    weight_kg: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user_data = UserInput(
            user_key=user_key.strip(),
            name=name.strip(),
            age=age,
            weight_kg=weight_kg,
            goal=goal,
            intensity=intensity,
        )
    except ValidationError as exc:
        error_message = "; ".join(
            f"{'.'.join(map(str, error['loc']))}: {error['msg']}"
            for error in exc.errors()
        )
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error": error_message},
            status_code=422,
        )

    workout, plan_mode = ai.generate_workout(user_data)
    tip, tip_mode = ai.nutrition_tip(user_data)
    user = save_user_and_plan(db, user_data, workout, tip)

    ai_mode = (
        plan_mode
        if plan_mode == tip_mode
        else f"Plan: {plan_mode}; tip: {tip_mode}"
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context=result_context(request, user, user.plans[0], ai_mode),
    )


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback_form(
    request: Request,
    user_key: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        data = FeedbackRequest(
            user_key=user_key.strip(),
            feedback=feedback.strip(),
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=exc.errors(),
        ) from exc

    user = get_user_with_plan(db, data.user_key)

    if user is None or not user.plans:
        raise HTTPException(
            status_code=404,
            detail="No plan was found for that user ID.",
        )

    plan_record = user.plans[0]
    profile = UserInput(
        user_key=user.user_key,
        name=user.name,
        age=user.age,
        weight_kg=user.weight_kg,
        goal=user.goal,
        intensity=user.intensity,
    )

    updated_plan, ai_mode = ai.update_workout(
        profile,
        plan_record.current_plan,
        data.feedback,
    )
    plan_record.current_plan = updated_plan
    plan_record.latest_feedback = data.feedback
    plan_record.nutrition_tip, _ = ai.nutrition_tip(profile)
    db.commit()

    context = result_context(request, user, plan_record, ai_mode)
    context["notice"] = "Your feedback has been applied."

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context=context,
    )


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(
    request: Request,
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "request": request,
            "users": all_users(db),
        },
    )


@router.post("/delete-user/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.get(models.User, user_id)

    if user:
        db.delete(user)
        db.commit()

    return RedirectResponse(
        url="/view-all-users",
        status_code=303,
    )


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post(
    "/api/plans",
    response_model=GenerateResponse,
    tags=["plans"],
)
def create_plan(
    data: UserInput,
    db: Session = Depends(get_db),
):
    workout, ai_mode = ai.generate_workout(data)
    tip, _ = ai.nutrition_tip(data)
    save_user_and_plan(db, data, workout, tip)

    return GenerateResponse(
        user_key=data.user_key,
        workout_plan=workout,
        nutrition_tip=tip,
        ai_mode=ai_mode,
    )


@router.post(
    "/api/plans/feedback",
    response_model=FeedbackResponse,
    tags=["plans"],
)
def revise_plan(
    data: FeedbackRequest,
    db: Session = Depends(get_db),
):
    user = get_user_with_plan(db, data.user_key)

    if user is None or not user.plans:
        raise HTTPException(
            status_code=404,
            detail="No plan was found for that user ID.",
        )

    plan_record = user.plans[0]
    profile = UserInput(
        user_key=user.user_key,
        name=user.name,
        age=user.age,
        weight_kg=user.weight_kg,
        goal=user.goal,
        intensity=user.intensity,
    )

    updated_plan, ai_mode = ai.update_workout(
        profile,
        plan_record.current_plan,
        data.feedback,
    )
    plan_record.current_plan = updated_plan
    plan_record.latest_feedback = data.feedback
    plan_record.nutrition_tip, _ = ai.nutrition_tip(profile)
    db.commit()

    return FeedbackResponse(
        user_key=data.user_key,
        workout_plan=updated_plan,
        nutrition_tip=plan_record.nutrition_tip,
        ai_mode=ai_mode,
    )


@router.get("/api/users", tags=["users"])
def list_users(db: Session = Depends(get_db)):
    users = all_users(db)

    return [
        {
            "id": user.id,
            "user_key": user.user_key,
            "name": user.name,
            "age": user.age,
            "weight_kg": user.weight_kg,
            "goal": user.goal,
            "intensity": user.intensity,
            "plans": [
                {
                    "original_plan": plan.original_plan,
                    "current_plan": plan.current_plan,
                    "nutrition_tip": plan.nutrition_tip,
                    "latest_feedback": plan.latest_feedback,
                }
                for plan in user.plans
            ],
        }
        for user in users
    ]