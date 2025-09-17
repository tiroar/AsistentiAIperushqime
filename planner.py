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
) -> Dict[str, Dict[str, Optional[Recipe]]]:
    """
    Diversity-aware picker:
      - No repeated recipe names in the week
      - Penalizes repeating the same main protein too often
      - Penalizes repeating yesterday’s protein for the same meal
      - Slightly rewards tag overlap
      - Chooses among the top-K candidates with a bit of randomness
    """
    rng = random.Random(seed)
    split = kcal_target_split(total_kcal, pattern)
    plan: Dict[str, Dict[str, Optional[Recipe]]] = {}

    used_names = set()                        # prevent exact duplicates in a week
    protein_count: Dict[str, int] = {}        # global protein usage
    last_protein_for_meal: Dict[str, str] = {"breakfast": "", "lunch": "", "dinner": ""}

    def _score(r: Recipe, meal_type: str) -> float:
        # 1) closeness to kcal target
        kcal_pen = abs(r.kcal - split[meal_type]) / 10.0   # every 10 kcal off = -1
        s = -kcal_pen

        # 2) never repeat exactly the same recipe
        if r.name in used_names:
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

        return s

    for day in DAYS:
        day_plan: Dict[str, Optional[Recipe]] = {}
        for meal_type in ["breakfast", "lunch", "dinner"]:
            pool = filter_recipes(recipes, meal_type, include_tags, exclude_keywords)

            # Choose with scoring + small randomness among top candidates
            if pool:
                ranked = sorted(pool, key=lambda r: _score(r, meal_type), reverse=True)
                K = 5 if len(ranked) >= 5 else len(ranked)
                chosen = rng.choice(ranked[:K]) if K > 0 else None
            else:
                chosen = None

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
