from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.schemas import UserInput


def save_user_and_plan(
    db: Session,
    data: UserInput,
    plan: str,
    tip: str,
) -> models.User:
    user = db.scalar(
        select(models.User).where(models.User.user_key == data.user_key)
    )

    if user is None:
        user = models.User(
            user_key=data.user_key,
            name=data.name,
            age=data.age,
            weight_kg=data.weight_kg,
            goal=data.goal,
            intensity=data.intensity,
        )
        db.add(user)
        db.flush()
    else:
        user.name = data.name
        user.age = data.age
        user.weight_kg = data.weight_kg
        user.goal = data.goal
        user.intensity = data.intensity

    record = db.scalar(
        select(models.WorkoutPlan).where(
            models.WorkoutPlan.user_id == user.id
        )
    )

    if record is None:
        record = models.WorkoutPlan(
            user_id=user.id,
            original_plan=plan,
            current_plan=plan,
            nutrition_tip=tip,
        )
        db.add(record)
    else:
        record.original_plan = plan
        record.current_plan = plan
        record.nutrition_tip = tip
        record.latest_feedback = None

    db.commit()
    db.refresh(user)
    return user


def get_user_with_plan(db: Session, user_key: str):
    return db.scalar(
        select(models.User)
        .options(selectinload(models.User.plans))
        .where(models.User.user_key == user_key)
    )


def all_users(db: Session):
    return db.scalars(
        select(models.User)
        .options(selectinload(models.User.plans))
        .order_by(models.User.created_at.desc())
    ).all()