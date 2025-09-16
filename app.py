import json
import pandas as pd
import streamlit as st
from planner import Recipe, make_week_plan, build_shopping_list, DAYS
from ai_helpers import suggest_substitutions, expand_recipe_request, translate_to_albanian, save_recipe_to_json

st.set_page_config(page_title="AI Meal Helper", page_icon="🍽️", layout="wide")

# --- Sidebar controls ---
st.sidebar.title("🤖 AI Features")

use_ai_subs = st.sidebar.checkbox("Enable Smart Substitutions", value=True)
use_ai_expand = st.sidebar.checkbox("Enable Recipe Expansion", value=False)
localize_albanian = st.sidebar.checkbox("Translate Instructions to Albanian", value=False)

pantry_input = st.sidebar.text_area(
    "Pantry items (comma-separated)",
    placeholder="rice, eggs, chicken"
)
pantry = [x.strip() for x in pantry_input.split(",") if x.strip()]

@st.cache_data
def load_recipes(path: str = "recipes.json"):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Recipe(**r) for r in raw]

recipes = load_recipes()

st.title("🍽️ AI Meal Planning Helper")
st.markdown(
    "Plan a healthy, realistic 7-day menu based on your calories, preferences, and exclusions. "
    "Export a grocery list in one click."
)

col1, col2, col3 = st.columns([1,1,1])
with col1:
    total_kcal = st.number_input("Daily calorie target", min_value=1200, max_value=4000, value=2200, step=50)
with col2:
    pattern = st.text_input("Meal calorie split (B/L/D)", value="30/40/30", help="Percentages like 30/40/30")
with col3:
    include_tags = st.multiselect(
        "Preference tags (soft filter)",
        options=sorted({t for r in recipes for t in r.tags}),
        default=[]
    )

excl = st.text_input("Exclude keywords (comma-separated, e.g. ‘pork, mushroom, spicy’)", value="")
exclude_keywords = [x.strip() for x in excl.split(",") if x.strip()]

st.divider()
if st.button("Generate 7-Day Plan", type="primary"):
    plan = make_week_plan(recipes, total_kcal, include_tags, exclude_keywords, pattern)
    st.success("Plan generated!")
        # --- AI Substitutions ---
    if use_ai_subs and pantry:
        st.subheader("✨ AI Substitutions")
        for day in DAYS:
            for meal_type, r in plan[day].items():
                if r:
                    subs = suggest_substitutions(r.ingredients, pantry)
                    with st.expander(f"Substitutions for {day} {meal_type.title()} ({r.name})"):
                        st.markdown(subs)
    # Show plan
    for day in DAYS:
        st.subheader(f"📅 {day}")
        meals = plan[day]
        cols = st.columns(3)
        for i, meal_type in enumerate(["breakfast","lunch","dinner"]):
            with cols[i]:
                r = meals[meal_type]
                if r:
                    st.markdown(f"**{meal_type.title()}** — *{r.name}*")
                    st.caption(f"{r.kcal} kcal • P {r.protein} / C {r.carbs} / F {r.fat} • tags: {', '.join(r.tags)}")
                    with st.expander("Ingredients"):
                        st.write("\n".join(f"• {x}" for x in r.ingredients))
                    with st.expander("Steps"):
                        steps = r.steps
                        if localize_albanian:
                            steps = [translate_to_albanian(step) for step in steps]
                        for idx, step in enumerate(steps, 1):
                            st.write(f"{idx}. {step}")
                    # Save AI-generated recipes button
                    if use_ai_expand and r and "AI" in getattr(r, "tags", []):
                        if st.button(f"💾 Save recipe: {r.name}", key=f"save_{day}_{meal_type}"):
                            saved = save_recipe_to_json(r.dict())
                            if saved:
                                st.success("✅ Recipe saved to recipes.json!")
                            else:
                                st.error("❌ Could not save recipe.")
                else:
                    st.warning(f"No {meal_type} found with your filters.")

    st.divider()
    # Shopping list
    shopping = build_shopping_list(plan)
    st.subheader("🛒 Consolidated Shopping List")
    df = pd.DataFrame(
        [{"Item": k, "Occurrences": v} for k, v in sorted(shopping.items(), key=lambda x: (-x[1], x[0]))]
    )
    st.dataframe(df, width="stretch", hide_index=True)

    # Download buttons
    st.download_button(
        "Download Shopping List (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="shopping_list.csv",
        mime="text/csv",
    )

    # Export weekly plan as CSV
    rows = []
    for day in DAYS:
        for meal_type in ["breakfast","lunch","dinner"]:
            r = plan[day][meal_type]
            rows.append({
                "Day": day,
                "Meal": meal_type.title(),
                "Recipe": r.name if r else "",
                "kcal": r.kcal if r else "",
                "protein": r.protein if r else "",
                "carbs": r.carbs if r else "",
                "fat": r.fat if r else ""
            })
    plan_df = pd.DataFrame(rows)
    st.download_button(
        "Download Weekly Plan (CSV)",
        data=plan_df.to_csv(index=False).encode("utf-8"),
        file_name="meal_plan.csv",
        mime="text/csv",
    )

else:
    st.info("Set your preferences and click **Generate 7-Day Plan**.")

st.markdown("---")
st.caption("Tip: Add more recipes to `recipes.json` for richer plans. You can tag recipes as `vegetarian`, `budget`, `high-protein`, `gluten-free`, etc.")
