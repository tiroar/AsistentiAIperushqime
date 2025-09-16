import os
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st
import json

from pathlib import Path
load_dotenv(dotenv_path=Path("andi.env"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@st.cache_data(show_spinner=False)
def suggest_substitutions(ingredients: list[str], pantry: list[str]) -> str:
    prompt = f"""
    The user has a pantry with: {', '.join(pantry)}.
    Suggest substitutions for these recipe ingredients: {', '.join(ingredients)}.
    Only suggest realistic food swaps that are common in cooking.
    Respond briefly as a bullet list: Ingredient → Suggested Substitute.
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful cooking assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content.strip()

@st.cache_data(show_spinner=False)
def expand_recipe_request(meal_type: str, kcal: int, tags: list[str], exclusions: list[str]) -> dict:
    prompt = f"""
    Create a new {meal_type} recipe ~{kcal} kcal.
    Must include tags: {', '.join(tags) if tags else 'any'}.
    Must exclude: {', '.join(exclusions) if exclusions else 'none'}.
    Return JSON with: name, ingredients, steps, kcal, protein, carbs, fat, tags.
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a recipe generator."},
            {"role": "user", "content": prompt},
        ],
    )
    import json
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"error": resp.choices[0].message.content}

@st.cache_data(show_spinner=False)
def translate_to_albanian(text: str) -> str:
    prompt = f"Translate this into clear, natural Albanian:\n{text}"
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a translator."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content.strip()

def save_recipe_to_json(recipe: dict, path: str = "recipes.json") -> bool:
    """Ruaj recetën e re në recipes.json"""
    try:
        file_path = Path(path)
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        data.append(recipe)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print(f"[SAVE ERROR] {e}")
        return False