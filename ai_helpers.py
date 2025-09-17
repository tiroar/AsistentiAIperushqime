import os
import json
from pathlib import Path
from typing import List, Dict, Optional

import streamlit as st
from openai import OpenAI

# ---- OpenAI client (graceful if missing) ----
API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
client: Optional[OpenAI] = OpenAI(api_key=API_KEY) if API_KEY else None

def _chat(system: str, user: str, model: str = "gpt-4o-mini", temperature: float = 0.2) -> Optional[str]:
    """Call OpenAI safely. Returns text or None on any error/missing key."""
    if not client:
        return None
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return None

# ---- AI helpers ----

@st.cache_data(show_spinner=False)
def suggest_substitutions(ingredients: List[str], pantry: List[str]) -> str:
    """AI-powered substitutions; falls back to a simple rule-based list."""
    prompt = (
        "The user has this pantry: " + ", ".join(pantry) + ".\n"
        "Suggest realistic cooking substitutions for these ingredients: "
        + ", ".join(ingredients) + ".\n"
        "Answer as a short bullet list: Ingredient → Suggested Substitute."
    )
    out = _chat(
        system="You are a practical home-cooking assistant. Prefer common swaps available in Albanian kitchens.",
        user=prompt,
        temperature=0.3,
    )
    if out:
        return out

    # Fallback (no API): naive matching to what the user has
    bullets = []
    pantry_lower = [p.lower() for p in pantry]
    for ing in ingredients:
        ing_l = ing.lower()
        # simple heuristic: suggest the first pantry item that shares a word root, else say "përdor çfarë ke"
        suggestion = next((p for p in pantry if any(tok and tok in ing_l for tok in p.lower().split())), None)
        suggestion = suggestion or (pantry[0] if pantry else "zëvendësim sipas shijes")
        bullets.append(f"• {ing} → {suggestion}")
    return "\n".join(bullets)

@st.cache_data(show_spinner=False)
def expand_recipe_request(meal_type: str, kcal: int, tags: List[str], exclusions: List[str]) -> Dict:
    """Ask AI to create a new recipe JSON; falls back to a simple template if AI unavailable."""
    prompt = (
        f"Create a new {meal_type} recipe ≈{kcal} kcal.\n"
        f"Must include tags: {', '.join(tags) if tags else 'any'}.\n"
        f"Must exclude: {', '.join(exclusions) if exclusions else 'none'}.\n"
        "Return strict JSON with fields: name, ingredients(list), steps(list), kcal, protein, carbs, fat, tags(list). "
        "Keep quantities metric."
    )
    out = _chat(
        system="You are a concise recipe generator that outputs valid JSON only.",
        user=prompt,
        temperature=0.5,
    )
    if out:
        try:
            data = json.loads(out)
            # Ensure minimal fields exist
            data.setdefault("tags", [])
            return data
        except Exception:
            return {"error": out}

    # Fallback (no API): simple deterministic template
    base_name = f"Simple {meal_type.title()} Bowl"
    return {
        "name": base_name,
        "ingredients": [
            "100 g oriz i zier",
            "150 g mish pule i pjekur (ose bishtajore për veg.)",
            "100 g perime të përziera",
            "1 lugë vaj ulliri",
            "Kripë, piper, limon"
        ],
        "steps": [
            "Ziej orizin sipas udhëzimit.",
            "Skuq ose pjek mishin e pulës; erëzo sipas shijes.",
            "Përziej me perime; shto vaj ulliri dhe limon.",
        ],
        "kcal": kcal,
        "protein": 30,
        "carbs": 60,
        "fat": 15,
        "tags": ["AI", *tags] if tags else ["AI"],
    }

@st.cache_data(show_spinner=False)
def translate_to_albanian(text: str) -> str:
    """Translate to Albanian; if AI is unavailable, return original text."""
    out = _chat(
        system="You are a precise translator to Albanian. Keep food names natural; preserve measures; be concise.",
        user=f"Translate to Albanian:\n{text}",
        temperature=0.2,
    )
    return out if out else text

# ---- Persistence ----

def save_recipe_to_json(recipe: Dict, path: str = "recipes.json") -> bool:
    """
    Ruaj recetën e re në recipes.json.
    - Nuk shton dublikatë (kontrollon name+meal_type, case-insensitive).
    - Shkruan në mënyrë atomike për të shmangur korruptimin e skedarit.
    """
    try:
        file_path = Path(path)

        # Lexo ekzistueset
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
        else:
            data = []

        # Normalizo çelësin unik: (name, meal_type)
        new_key = (
            (recipe.get("name") or "").strip().lower(),
            (recipe.get("meal_type") or "").strip().lower(),
        )

        # Kontrollo nëse ekziston
        for r in data:
            key = (
                (r.get("name") or "").strip().lower(),
                (r.get("meal_type") or "").strip().lower(),
            )
            if key == new_key:
                return True  # tashmë ekziston → mos shto dublikatë

        # Shto "AI" te tags nëse s’është aty (opsionale)
        tags = recipe.get("tags") or []
        if isinstance(tags, list) and "AI" not in [t for t in tags]:
            tags.append("AI")
            recipe["tags"] = tags

        # Shto recetën e re
        data.append(recipe)

        # Shkruaj në mënyrë atomike
        tmp_path = file_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp_path.replace(file_path)

        return True
    except Exception as e:
        print(f"[SAVE ERROR] {e}")
        return False
