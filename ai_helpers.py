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
def expand_recipe_request(meal_type: str, kcal: int, tags: List[str], exclusions: List[str], cooking_skill: str = "beginner") -> Dict:
    """Ask AI to create a new recipe JSON; falls back to a simple template if AI unavailable."""
    
    # Add cooking skill instructions
    skill_instructions = ""
    if cooking_skill == "beginner":
        skill_instructions = "Make it simple with basic techniques, clear steps, and common ingredients. "
    elif cooking_skill == "intermediate":
        skill_instructions = "Use moderate techniques with some complexity. "
    elif cooking_skill == "advanced":
        skill_instructions = "Use advanced techniques, complex flavors, and sophisticated methods. "
    
        prompt = (
            f"Create a new {meal_type} recipe ≈{kcal} kcal.\n"
            f"Must include tags: {', '.join(tags) if tags else 'any'}.\n"
            f"Must exclude: {', '.join(exclusions) if exclusions else 'none'}.\n"
            f"Cooking skill level: {cooking_skill}. {skill_instructions}"
            "Return strict JSON with fields: name, ingredients(list), steps(list), kcal, protein, carbs, fat, tags(list). "
            "CRITICAL: Each ingredient MUST include specific portion sizes in grams/ml/spoons/etc. "
            "Examples: '200g chicken breast', '150ml milk', '2 tbsp olive oil', '1 tsp salt'. "
            "Keep quantities metric. Make ingredients and steps appropriate for the skill level."
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

    # Fallback (no API): skill-appropriate template
    if cooking_skill == "beginner":
        base_name = f"Simple {meal_type.title()} Bowl"
        ingredients = [
            "100 g oriz i zier",
            "150 g mish pule i pjekur (ose bishtajore për veg.)",
            "100 g perime të përziera",
            "1 lugë vaj ulliri",
            "Kripë, piper, limon"
        ]
        steps = [
            "Ziej orizin sipas udhëzimit.",
            "Skuq ose pjek mishin e pulës; erëzo sipas shijes.",
            "Përziej me perime; shto vaj ulliri dhe limon.",
        ]
    elif cooking_skill == "intermediate":
        base_name = f"Mediterranean {meal_type.title()}"
        ingredients = [
            "120 g oriz i zier",
            "180 g mish pule i marinë",
            "150 g perime të përziera",
            "2 lugë vaj ulliri",
            "Barishte të freskëta, kripë, piper"
        ]
        steps = [
            "Marino mishin me barishte dhe vaj për 30 min.",
            "Ziej orizin dhe përgatit perimet.",
            "Pjek mishin dhe shërbej me oriz dhe perime.",
        ]
    else:  # advanced
        base_name = f"Gourmet {meal_type.title()}"
        ingredients = [
            "100 g oriz arborio",
            "200 g mish pule i marinë",
            "200 g perime të përziera",
            "3 lugë vaj ulliri",
            "Barishte të freskëta, kripë, piper, erëza"
        ]
        steps = [
            "Marino mishin me barishte komplekse për 2 orë.",
            "Gatit orizin me teknikë risotto.",
            "Pjek mishin me teknikë të avancuar dhe shërbej.",
        ]
    
    return {
        "name": base_name,
        "ingredients": ingredients,
        "steps": steps,
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

def enrich_recipe_with_portions(recipe: Dict) -> Dict:
    """Enrich a recipe by adding portion sizes to ingredients that don't have them"""
    if not recipe.get('ingredients'):
        return recipe
    
    enriched_ingredients = []
    for ingredient in recipe['ingredients']:
        # Check if ingredient already has measurements
        if any(unit in ingredient.lower() for unit in ['g', 'ml', 'tbsp', 'tsp', 'cup', 'oz', 'lb', 'kg', 'l', 'piece', 'pcs']):
            enriched_ingredients.append(ingredient)
        else:
            # Try to add appropriate portion size based on ingredient type
            enriched_ingredient = _suggest_portion_size(ingredient)
            enriched_ingredients.append(enriched_ingredient)
    
    recipe['ingredients'] = enriched_ingredients
    return recipe

def _suggest_portion_size(ingredient: str) -> str:
    """Suggest appropriate portion size for an ingredient"""
    ingredient_lower = ingredient.lower().strip()
    
    # Common portion suggestions based on ingredient type
    portion_suggestions = {
        # Spices and seasonings
        'salt': '1 tsp salt',
        'pepper': '1/2 tsp pepper',
        'paprika': '1 tsp paprika',
        'garlic': '2 cloves garlic',
        'onion': '1 medium onion',
        'garlic powder': '1/2 tsp garlic powder',
        'oregano': '1 tsp oregano',
        'basil': '1 tbsp fresh basil',
        'thyme': '1 tsp thyme',
        'rosemary': '1 tsp rosemary',
        'cumin': '1/2 tsp cumin',
        'cinnamon': '1/2 tsp cinnamon',
        'ginger': '1 tsp fresh ginger',
        'chili': '1 tsp chili powder',
        'cayenne': '1/4 tsp cayenne',
        'nutmeg': '1/4 tsp nutmeg',
        'vanilla': '1 tsp vanilla extract',
        
        # Vegetables
        'tomato': '2 medium tomatoes',
        'carrot': '1 large carrot',
        'potato': '2 medium potatoes',
        'broccoli': '200g broccoli',
        'spinach': '100g spinach',
        'lettuce': '100g lettuce',
        'cucumber': '1 medium cucumber',
        'bell pepper': '1 bell pepper',
        'mushroom': '150g mushrooms',
        'zucchini': '1 medium zucchini',
        'eggplant': '1 medium eggplant',
        'cabbage': '200g cabbage',
        'cauliflower': '300g cauliflower',
        
        # Proteins
        'chicken': '200g chicken breast',
        'beef': '200g beef',
        'pork': '200g pork',
        'fish': '200g fish fillet',
        'salmon': '200g salmon',
        'tuna': '150g tuna',
        'eggs': '2 large eggs',
        'tofu': '200g tofu',
        'cheese': '100g cheese',
        'yogurt': '200g yogurt',
        'milk': '250ml milk',
        
        # Grains and carbs
        'rice': '100g rice',
        'pasta': '100g pasta',
        'bread': '2 slices bread',
        'quinoa': '80g quinoa',
        'oats': '50g oats',
        'flour': '200g flour',
        'sugar': '2 tbsp sugar',
        'honey': '2 tbsp honey',
        'oil': '2 tbsp olive oil',
        'butter': '1 tbsp butter',
        'olive oil': '2 tbsp olive oil',
        'coconut oil': '1 tbsp coconut oil',
        
        # Nuts and seeds
        'almonds': '30g almonds',
        'walnuts': '30g walnuts',
        'peanuts': '30g peanuts',
        'sesame': '1 tbsp sesame seeds',
        'sunflower': '1 tbsp sunflower seeds',
        'chia': '1 tbsp chia seeds',
        'flax': '1 tbsp flax seeds',
    }
    
    # Try to find a match
    for key, suggestion in portion_suggestions.items():
        if key in ingredient_lower:
            return suggestion
    
    # Default fallback - add a generic portion
    if 'sauce' in ingredient_lower:
        return f"2 tbsp {ingredient}"
    elif 'spice' in ingredient_lower or 'herb' in ingredient_lower:
        return f"1 tsp {ingredient}"
    elif 'vegetable' in ingredient_lower or 'veggie' in ingredient_lower:
        return f"150g {ingredient}"
    else:
        return f"1 portion {ingredient}"

def generate_personalized_recipe(meal_type: str, kcal: int, user_preferences: Dict, 
                                cooking_skill: str = "beginner", tags: List[str] = None) -> Dict:
    """Generate a personalized recipe based on user preferences and cooking skill."""
    
    # Analyze user preferences
    favorite_ingredients = []
    disliked_ingredients = []
    
    if user_preferences:
        for food, data in user_preferences.items():
            rating = data.get('avg_rating', 3.0)
            if rating >= 4.0:
                favorite_ingredients.append(food)
            elif rating <= 2.0:
                disliked_ingredients.append(food)
    
    # Create personalized prompt
    preference_text = ""
    if favorite_ingredients:
        preference_text += f"User loves these ingredients: {', '.join(favorite_ingredients[:5])}. "
    if disliked_ingredients:
        preference_text += f"User dislikes these ingredients: {', '.join(disliked_ingredients[:3])}. "
    
    skill_instructions = ""
    if cooking_skill == "beginner":
        skill_instructions = "Make it simple with basic techniques, clear steps, and common ingredients. "
    elif cooking_skill == "intermediate":
        skill_instructions = "Use moderate techniques with some complexity. "
    elif cooking_skill == "advanced":
        skill_instructions = "Use advanced techniques, complex flavors, and sophisticated methods. "
    
    prompt = (
        f"Create a personalized {meal_type} recipe ≈{kcal} kcal.\n"
        f"{preference_text}"
        f"Cooking skill level: {cooking_skill}. {skill_instructions}"
        f"Tags to include: {', '.join(tags) if tags else 'any'}.\n"
        "Return strict JSON with fields: name, ingredients(list), steps(list), kcal, protein, carbs, fat, tags(list). "
        "CRITICAL: Each ingredient MUST include specific portion sizes in grams/ml/spoons/etc. "
        "Examples: '200g chicken breast', '150ml milk', '2 tbsp olive oil', '1 tsp salt'. "
        "Make it personalized and appealing to the user's taste preferences."
    )
    
    out = _chat(
        system="You are a personalized recipe generator that creates recipes based on user preferences and cooking skill level.",
        user=prompt,
        temperature=0.6,  # Higher temperature for more creativity
    )
    
    if out:
        try:
            data = json.loads(out)
            data.setdefault("tags", [])
            data["tags"].extend(["AI", "personalized"])
            return data
        except Exception:
            return {"error": out}
    
    # Fallback to basic recipe generation
    return expand_recipe_request(meal_type, kcal, tags or [], [], cooking_skill)

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
