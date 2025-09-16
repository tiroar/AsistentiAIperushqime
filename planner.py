from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import random
import math

class Recipe(BaseModel):
    name: str
    meal_type: str  # breakfast/lunch/dinner
    kcal: int
    protein: int
    carbs: int
    fat: int
    tags: List[str]
    ingredients: List[str]
    steps: List[str]

DAYS = ["E Hënë","E Martë","E Mërkurë","E Enjte","E Premte","E Shtunë","E Diel"]

def filter_recipes(
    recipes: List[Recipe],
    meal_type: str,
    include_tags: List[str],
    exclude_keywords: List[str],
) -> List[Recipe]:
    def ok(r: Recipe) -> bool:
        if r.meal_type != meal_type:
            return False
        # include_tags are soft filters: if set, prefer recipes containing them
        # exclude_keywords: hard filter on name/ingredients
        text = (r.name + " " + " ".join(r.ingredients)).lower()
        for bad in exclude_keywords:
            if bad.strip() and bad.lower() in text:
                return False
        return True

    pool = [r for r in recipes if ok(r)]
    if include_tags:
        preferred = [r for r in pool if any(t in r.tags for t in include_tags)]
        return preferred if preferred else pool
    return pool

def kcal_target_split(total_kcal: int, pattern: str = "30/40/30") -> Dict[str, int]:
    # pattern is B/L/D percentage
    try:
        b, l, d = [int(x) for x in pattern.split("/")]
        factor = total_kcal / (b + l + d)
        return {
            "breakfast": int(round(b * factor)),
            "lunch": int(round(l * factor)),
            "dinner": int(round(d * factor)),
        }
    except Exception:
        # fallback 30/40/30
        return kcal_target_split(total_kcal, "30/40/30")

def pick_meal(recipes: List[Recipe], target_kcal: int) -> Optional[Recipe]:
    if not recipes:
        return None
    # pick the meal with kcal closest to target
    recipes_sorted = sorted(recipes, key=lambda r: abs(r.kcal - target_kcal))
    # add a bit of variety
    top = recipes_sorted[:min(5, len(recipes_sorted))]
    return random.choice(top)

def make_week_plan(
    recipes: List[Recipe],
    total_kcal: int,
    include_tags: List[str],
    exclude_keywords: List[str],
    pattern: str = "30/40/30",
) -> Dict[str, Dict[str, Optional[Recipe]]]:
    split = kcal_target_split(total_kcal, pattern)
    plan: Dict[str, Dict[str, Optional[Recipe]]] = {}
    used_names = set()  # To reduce repeats

    for day in DAYS:
        day_plan: Dict[str, Optional[Recipe]] = {}
        for meal_type in ["breakfast", "lunch", "dinner"]:
            pool = filter_recipes(recipes, meal_type, include_tags, exclude_keywords)
            pool = [r for r in pool if r.name not in used_names] or pool
            chosen = pick_meal(pool, split[meal_type])

            # --- AI expansion if no recipe available ---
            if not chosen:
                try:
                    from ai_helpers import expand_recipe_request
                    ai_recipe = expand_recipe_request(meal_type, split[meal_type], include_tags, exclude_keywords)
                    if ai_recipe and "name" in ai_recipe:
                        chosen = Recipe(
                            name=ai_recipe["name"],
                            meal_type=meal_type,
                            kcal=ai_recipe.get("kcal", split[meal_type]),
                            protein=ai_recipe.get("protein", 0),
                            carbs=ai_recipe.get("carbs", 0),
                            fat=ai_recipe.get("fat", 0),
                            tags=ai_recipe.get("tags", []) + ["AI"],
                            ingredients=ai_recipe.get("ingredients", []),
                            steps=ai_recipe.get("steps", []),
                        )
                except Exception as e:
                    print(f"[AI Expansion Error] {e}")

            day_plan[meal_type] = chosen
            if chosen:
                used_names.add(chosen.name)
        plan[day] = day_plan

    return plan

def build_shopping_list(plan: Dict[str, Dict[str, Optional[Recipe]]]) -> Dict[str, int]:
    # super simple aggregation by line; you can improve with NLP units parsing later
    counts: Dict[str, int] = {}
    for _, meals in plan.items():
        for meal in meals.values():
            if not meal:
                continue
            for line in meal.ingredients:
                key = line.strip()
                counts[key] = counts.get(key, 0) + 1
    return counts
