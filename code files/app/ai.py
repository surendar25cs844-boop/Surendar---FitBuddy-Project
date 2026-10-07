from google import genai

from app.config import settings
from app.schemas import UserInput


def _generate(model: str, prompt: str) -> str:
    if not settings.google_api_key:
        raise RuntimeError("Gemini API key is not configured")

    client = genai.Client(api_key=settings.google_api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    text = (response.text or "").strip()

    if not text:
        raise RuntimeError("Gemini returned an empty response")

    return text


def _profile(user: UserInput) -> str:
    return (
        f"Name: {user.name}; age: {user.age}; weight: {user.weight_kg:g} kg; "
        f"goal: {user.goal.replace('_', ' ')}; "
        f"preferred intensity: {user.intensity}."
    )


def local_workout(user: UserInput, feedback: str | None = None) -> str:
    focus = {
        "weight_loss": "moderate cardio and full-body strength",
        "muscle_gain": "progressive resistance training",
        "general_wellness": "balanced strength, cardio, and mobility",
        "flexibility": "mobility, flexibility, and light conditioning",
    }[user.goal]

    level = {
        "low": "Beginner",
        "medium": "Intermediate",
        "high": "Advanced",
    }[user.intensity]

    days = [
        ("Full body strength", "Chair or bodyweight squats, incline push-ups, glute bridges"),
        ("Cardio and mobility", "Brisk walk or cycling, hip and shoulder mobility"),
        ("Upper body and core", "Band rows, wall push-ups, dead bugs"),
        ("Recovery", "Easy walk and gentle full-body stretching"),
        ("Lower body strength", "Step-ups, hip hinges, calf raises"),
        ("Steady cardio", "Comfortable walk, cycle, or swim"),
        ("Rest and reflection", "Rest; note energy, soreness, and progress"),
    ]

    rows = [
        f"7-Day Plan — {level} | Focus: {focus}",
        f"Profile: {user.age} years, {user.weight_kg:g} kg",
        "",
        "Start active days with a 5–10 minute warm-up. Keep good form and stop if you feel pain or dizziness.",
    ]

    for number, (title, moves) in enumerate(days, 1):
        rows.extend([
            "",
            f"Day {number}: {title}",
            f"• {moves}",
            "• Strength: 2–3 sets of 8–12 controlled reps; rest 60–90 seconds.",
            "• Finish with a 5-minute cooldown and relaxed stretching.",
        ])

    if feedback:
        rows.extend([
            "",
            f"Update applied: {feedback}",
            "Adjust activity gradually and keep at least one recovery day.",
        ])

    return "\n".join(rows)


def generate_workout(user: UserInput) -> tuple[str, str]:
    try:
        prompt = (
            "Create a safe, practical 7-day fitness plan using this profile. "
            "Include warm-up, exercises with sets/reps or duration, rest, and "
            "cooldown for each day. Include at least one recovery day. Avoid "
            "extreme dieting and medical claims. Advise stopping for pain or "
            "dizziness.\n"
            + _profile(user)
        )
        return _generate(settings.gemini_plan_model, prompt), "Gemini"
    except Exception:
        return local_workout(user), "Built-in sample (Gemini unavailable)"


def update_workout(
    user: UserInput,
    plan: str,
    feedback: str,
) -> tuple[str, str]:
    try:
        prompt = (
            "Revise this 7-day fitness plan according to the user's feedback. "
            "Keep it safe and realistic, preserve recovery time, and do not "
            "follow dangerous requests.\n"
            f"Profile: {_profile(user)}\n"
            f"Current plan:\n{plan}\n"
            f"Feedback:\n{feedback}"
        )
        return _generate(settings.gemini_plan_model, prompt), "Gemini"
    except Exception:
        return local_workout(user, feedback), "Built-in sample (Gemini unavailable)"


def nutrition_tip(user: UserInput) -> tuple[str, str]:
    try:
        prompt = (
            "Give one concise, practical nutrition or recovery tip for this "
            "fitness goal. Avoid calorie prescriptions, medical claims, and "
            "supplement claims. Mention that individual needs vary.\n"
            + _profile(user)
        )
        return _generate(settings.gemini_tip_model, prompt), "Gemini"
    except Exception:
        tips = {
            "weight_loss": (
                "Build meals around vegetables, a satisfying protein source, "
                "and foods you enjoy. Sustainable habits matter more than "
                "quick fixes."
            ),
            "muscle_gain": (
                "Include a protein-rich food in meals and consider a balanced "
                "snack after training if it suits your routine."
            ),
            "general_wellness": (
                "Eat a varied mix of foods, drink to thirst, and prioritize "
                "consistent sleep and recovery."
            ),
            "flexibility": (
                "Support mobility sessions with regular hydration, balanced "
                "meals, and rest between harder sessions."
            ),
        }
        return tips[user.goal], "Built-in sample (Gemini unavailable)"