import json
import pandas as pd
import streamlit as st
from planner import Recipe, make_week_plan, build_shopping_list, DAYS
from ai_helpers import suggest_substitutions, expand_recipe_request, translate_to_albanian, save_recipe_to_json
from PIL import Image
icon = Image.open("images/icon.png")

st.set_page_config(page_title="AI Meal Helper", page_icon=icon, layout="wide")


@st.cache_data
def load_recipes(path: str = "recipes.json"):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Recipe(**r) for r in raw]

recipes = load_recipes()

# --- Helpers: TDEE / Protein & Macro targets ---
def calc_tdee_kcal(gender: str, age: int, height_cm: int, weight_kg: float, activity: str, goal: str) -> tuple[int, int]:
    # Mifflin–St Jeor BMR
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if gender == "Male" else -161)
    mult = {
        "Sedentary (office work)": 1.2,
        "Moderate (3-4x/week)": 1.55,
        "Active (5-6x/week)": 1.725,
    }[activity]
    tdee = bmr * mult
    goal_adj = {"Weight loss": 0.85, "Maintenance": 1.0, "Muscle gain": 1.10}[goal]
    kcal = int(round(tdee * goal_adj))

    # Daily protein (g) based on goal (based on body weight)
    g_per_kg = {"Weight loss": 1.7, "Maintenance": 1.4, "Muscle gain": 1.8}[goal]
    protein_g = int(round(g_per_kg * weight_kg))
    return kcal, protein_g

def macro_split_for_goal(goal: str) -> tuple[int, int, int]:
    # Returns percentages (P, C, F) based on goal
    if goal == "Weight loss":
        return (30, 40, 30)  # Protein/ Carbs/ Fat
    if goal == "Muscle gain":
        return (30, 50, 20)
    return (25, 50, 25)     # Maintenance (default)

def macro_targets_grams(total_kcal: int, goal: str, protein_g_from_weight: int) -> tuple[int, int, int]:
    p_pct, c_pct, f_pct = macro_split_for_goal(goal)
    # Calculate from %:
    p_kcal = total_kcal * p_pct / 100
    c_kcal = total_kcal * c_pct / 100
    f_kcal = total_kcal * f_pct / 100

    p_g_pct = int(round(p_kcal / 4))
    c_g = int(round(c_kcal / 4))
    f_g = int(round(f_kcal / 9))

    # Use maximum between protein based on weight and that from %
    p_g = max(protein_g_from_weight, p_g_pct)
    return p_g, c_g, f_g

st.title("🍽️ AI Meal Planning Helper")
st.markdown(
    "Plan a healthy, realistic 7-day menu based on your calories, preferences, and exclusions. "
    "Export a grocery list in one click."
)

# --- Profile & Goals (automatic calorie recommendation) ---
with st.expander("🧍‍♂️ Profile & Goals (automatic calorie recommendation)", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        gender = st.selectbox("Gender", ["Male", "Female"], index=0)
    with c2:
        age = st.number_input("Age", min_value=14, max_value=90, value=28, step=1)
    with c3:
        height_cm = st.number_input("Height (cm)", min_value=130, max_value=220, value=178, step=1)
    with c4:
        weight_kg = st.number_input("Weight (kg)", min_value=35.0, max_value=250.0, value=78.0, step=0.5)

    activity = st.selectbox(
        "Daily activity level",
        ["Sedentary (office work)", "Moderate (3-4x/week)", "Active (5-6x/week)"],
        index=0
    )
    goal = st.radio("Goal", ["Weight loss", "Maintenance", "Muscle gain"], index=0, horizontal=True)

    suggested_kcal, suggested_protein = calc_tdee_kcal(gender, age, height_cm, weight_kg, activity, goal)
    # Target macronutrients in grams (based on kcal & goal, with protein >= based on weight)
    target_p_g, target_c_g, target_f_g = macro_targets_grams(suggested_kcal, goal, suggested_protein)

    use_auto_kcal = st.checkbox("Use automatic recommendation", value=True)
    st.caption(
        f"Recommendation: **{suggested_kcal} kcal/day** • "
        f"Macronutrients: **P {target_p_g} g / C {target_c_g} g / F {target_f_g} g** "
        f"(protein min. based on weight: ~{suggested_protein} g)"
    )

# Default value for calorie field
_default_kcal = suggested_kcal if use_auto_kcal else 2200

col1, col2, col3 = st.columns([1,1,1])
with col1:
    total_kcal = st.number_input("Daily calorie target", min_value=1200, max_value=4000, value=_default_kcal, step=50)
with col2:
    pattern = st.text_input("Meal calorie split (B/L/D)", value="30/40/30", help="Percentages like 30/40/30")
with col3:
    include_tags = st.multiselect(
        "Preference tags (soft filter)",
        options=sorted({t for r in recipes for t in r.tags}),
        default=[]
    )

excl = st.text_input("Exclude keywords (comma-separated, e.g. 'pork, mushroom, spicy')", value="")
exclude_keywords = [x.strip() for x in excl.split(",") if x.strip()]

# --- Additional controls (mobile-friendly) ---
with st.expander("⚙️ Additional features", expanded=False):
    use_ai_subs = st.checkbox("Enable Smart Substitutions", value=True, key="subs_main")
    use_ai_expand = st.checkbox("Enable Recipe Generation", value=False, key="expand_main")
    localize_albanian = st.checkbox("Translate everything to Albanian", value=False, key="sq_main")

    pantry_input = st.text_area(
        "What you have at home (comma-separated)",
        placeholder="rice, eggs, chicken breast",
        key="pantry_main"
    )

pantry = [x.strip() for x in pantry_input.split(",") if x.strip()]

st.divider()

# Store the plan in session state to prevent refresh issues
if 'meal_plan' not in st.session_state:
    st.session_state.meal_plan = None

if st.button("Generate 7-Day Plan", type="primary"):
    plan = make_week_plan(recipes, total_kcal, include_tags, exclude_keywords, pattern)
    st.session_state.meal_plan = plan
    st.success("Plan generated!")

# Display the plan if it exists in session state
if st.session_state.meal_plan:
    plan = st.session_state.meal_plan
    
    # --- Show daily objective (from Profile) ---
    # Recalculate based on final total_kcal (if user changes it manually)
    adj_p_g, adj_c_g, adj_f_g = macro_targets_grams(total_kcal, goal, suggested_protein)
    st.info(
        f"🎯 Daily objective: **{total_kcal} kcal** • "
        f"Macros: **P {adj_p_g} g / C {adj_c_g} g / F {adj_f_g} g**",
        icon="✅"
    )

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

    # Download buttons - Fixed encoding
    st.download_button(
        "Download Shopping List (CSV)",
        data=df.to_csv(index=False, encoding='utf-8-sig'),
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
        data=plan_df.to_csv(index=False, encoding='utf-8-sig'),
        file_name="meal_plan.csv",
        mime="text/csv",
    )

else:
    st.info("Set your preferences and click **Generate 7-Day Plan**.")

st.markdown("---")
st.caption("Tip: Add more recipes to `recipes.json` for richer plans. You can tag recipes as `vegetarian`, `budget`, `high-protein`, `gluten-free`, etc.")
