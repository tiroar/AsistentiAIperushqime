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

# ---------- Filtering ----------

def filter_recipes(
    recipes: List[Recipe],
    meal_type: str,
    include_tags: List[str],
    exclude_keywords: List[str],
) -> List[Recipe]:
    def ok(r: Recipe) -> bool:
        if r.meal_type != meal_type:
            return False
        # hard exclude on name/ingredients
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

# ---------- Energy split ----------

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

# ---------- Diversity helpers ----------

def _main_protein(r: Recipe) -> str:
    """Guess the main protein from name/ingredients/tags."""
    keywords = [
        "chicken","pulë","pule",
        "beef","viç","vici",
        "pork","derr",
        "turkey","gjeldeti",
        "fish","peshk","tuna","salmon","troftë","sarde",
        "shrimp","karkalec",
        "egg","vezë","veze",
        "tofu","tempeh",
        "beans","fasule","chickpea","qiqra","lentil","thjerrëz","thjerrez",
        "cheese","djath","yogurt","kos"
    ]
    hay = " ".join([r.name] + r.ingredients + r.tags).lower()
    for k in keywords:
        if k in hay:
            return k
    return "other"

# ---------- Planner ----------

def make_week_plan(
    recipes: List[Recipe],
    total_kcal: int,
    include_tags: List[str],
    exclude_keywords: List[str],
    pattern: str = "30/40/30",
    seed: Optional[int] = None,
    use_ai_expand: bool = True,
    auto_save_ai: bool = True,
    user_preferences: Optional[Dict] = None,
    cooking_skill: str = "beginner",
) -> Dict[str, Dict[str, Optional[Recipe]]]:
    """
    Diversity-aware picker + AI enrichment:

      - No repeated recipe names in the week (global + per-meal)
      - Penalizes repeating the same main protein too often
      - Penalizes repeating yesterday’s protein for the *same* meal
      - Rewards preference-tag overlap
      - Chooses among the top-K with a bit of randomness
      - If pool is empty OR sometimes for variety, generates a new AI recipe
      - Saves AI recipes directly into recipes.json (de-duped)
    """
    rng = random.Random(seed)
    split = kcal_target_split(total_kcal, pattern)
    plan: Dict[str, Dict[str, Optional[Recipe]]] = {}

    used_names_global: set[str] = set()                          # prevent exact duplicates in a week
    used_names_by_meal: Dict[str, set[str]] = {m: set() for m in ["breakfast", "lunch", "dinner"]}
    protein_count: Dict[str, int] = {}                            # global protein usage
    last_protein_for_meal: Dict[str, str] = {"breakfast": "", "lunch": "", "dinner": ""}

    def _score(r: Recipe, meal_type: str) -> float:
        # 1) closeness to kcal target
        kcal_pen = abs(r.kcal - split[meal_type]) / 10.0   # every 10 kcal off = -1
        s = -kcal_pen

        # 2) never repeat exactly the same recipe
        if r.name in used_names_global or r.name in used_names_by_meal[meal_type]:
            s -= 100.0

        # 3) protein diversity
        prot = _main_protein(r)
        s -= protein_count.get(prot, 0) * 0.8               # global repetition penalty
        if last_protein_for_meal[meal_type] == prot:
            s -= 0.8                                        # avoid same protein as yesterday for this meal

        # 4) reward preference-tag overlap
        if include_tags:
            overlap = len(set(r.tags) & set(include_tags))
            s += 0.3 * overlap

        # 5) user preference learning bonus
        if user_preferences:
            for ingredient in r.ingredients:
                ingredient_name = ingredient.lower().split()[0]  # Get main ingredient name
                for pref_item, pref_data in user_preferences.items():
                    if ingredient_name in pref_item.lower() or pref_item.lower() in ingredient_name:
                        rating = pref_data.get('avg_rating', 3.0)
                        confidence = min(pref_data.get('count', 1) / 5.0, 1.0)  # Confidence based on rating count
                        s += (rating - 3.0) * 0.2 * confidence  # Bonus for liked foods, penalty for disliked

        # 6) cooking skill adaptation bonus
        if cooking_skill == "beginner" and any(tag in r.tags for tag in ["quick", "easy", "simple"]):
            s += 0.5
        elif cooking_skill == "advanced" and any(tag in r.tags for tag in ["complex", "advanced", "gourmet"]):
            s += 0.5

        return s

    for day in DAYS:
        day_plan: Dict[str, Optional[Recipe]] = {}

        for meal_type in ["breakfast", "lunch", "dinner"]:
            # Base pool after filters
            pool = filter_recipes(recipes, meal_type, include_tags, exclude_keywords)

            # Remove already used names (global + per-meal)
            pool = [
                r for r in pool
                if r.name not in used_names_global and r.name not in used_names_by_meal[meal_type]
            ]

            chosen: Optional[Recipe] = None

            # Rank by score, then pick among top-K (variety K=5 or less)
            if pool:
                ranked = sorted(pool, key=lambda r: _score(r, meal_type), reverse=True)
                K = min(5, len(ranked))
                chosen = rng.choice(ranked[:K]) if K > 0 else None

            # Decide if we want a fresh AI recipe for variety:
            # - if none chosen, we need AI
            # - otherwise, 25% chance to inject novelty when allowed
            need_ai = chosen is None
            if use_ai_expand and not need_ai:
                need_ai = (rng.random() < 0.25)

            if use_ai_expand and need_ai:
                try:
                    from ai_helpers import expand_recipe_request, save_recipe_to_json
                    # Add cooking skill to tags for AI generation
                    skill_tags = include_tags.copy() if include_tags else []
                    if cooking_skill == "beginner":
                        skill_tags.extend(["quick", "easy", "simple"])
                    elif cooking_skill == "advanced":
                        skill_tags.extend(["complex", "advanced", "gourmet"])
                    
                    ai_recipe = expand_recipe_request(meal_type, split[meal_type], skill_tags, exclude_keywords)
                    if ai_recipe and "name" in ai_recipe:
                        chosen = Recipe(
                            name=ai_recipe["name"],
                            meal_type=meal_type,
                            kcal=ai_recipe.get("kcal", split[meal_type]),
                            protein=ai_recipe.get("protein", 0),
                            carbs=ai_recipe.get("carbs", 0),
                            fat=ai_recipe.get("fat", 0),
                            tags=(ai_recipe.get("tags", []) or []) + ["AI"],
                            ingredients=ai_recipe.get("ingredients", []),
                            steps=ai_recipe.get("steps", []),
                        )
                        if auto_save_ai:
                            # persist directly to recipes.json (function handles de-dupe)
                            try:
                                save_recipe_to_json(chosen.dict(), path="recipes.json")
                            except Exception as e:
                                print(f"[AI Save Warning] {e}")
                except Exception as e:
                    print(f"[AI Expansion Error] {e}")

            day_plan[meal_type] = chosen

            if chosen:
                used_names_global.add(chosen.name)
                used_names_by_meal[meal_type].add(chosen.name)
                prot = _main_protein(chosen)
                protein_count[prot] = protein_count.get(prot, 0) + 1
                last_protein_for_meal[meal_type] = prot

        plan[day] = day_plan

    return plan

# ---------- Shopping list ----------

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
