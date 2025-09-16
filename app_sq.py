import json
import pandas as pd
import streamlit as st
from planner import Recipe, make_week_plan, build_shopping_list, DAYS
from ai_helpers import suggest_substitutions, expand_recipe_request, translate_to_albanian, save_recipe_to_json
from PIL import Image
icon = Image.open("images/icon.png")

st.set_page_config(page_title="Asistenti i Ushqimeve me AI", page_icon=icon, layout="wide")

@st.cache_data
def load_recipes(path: str = "recipes.json"):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Recipe(**r) for r in raw]

recipes = load_recipes()

# --- Helpers: TDEE / Protein & Macro targets ---
def calc_tdee_kcal(gender: str, age: int, height_cm: int, weight_kg: float, activity: str, goal: str) -> tuple[int, int]:
    # Mifflin–St Jeor BMR
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if gender == "Mashkull" else -161)
    mult = {
        "Në zyrë (pak aktiv)": 1.2,
        "Mesatar (3-4x/ javë)": 1.55,
        "Sportist (5-6x/ javë)": 1.725,
    }[activity]
    tdee = bmr * mult
    goal_adj = {"Humbje peshe": 0.85, "Mbajtje": 1.0, "Shtim muskuj": 1.10}[goal]
    kcal = int(round(tdee * goal_adj))

    # Proteina ditore (g) sipas qëllimit (bazuar në peshë trupore)
    g_per_kg = {"Humbje peshe": 1.7, "Mbajtje": 1.4, "Shtim muskuj": 1.8}[goal]
    protein_g = int(round(g_per_kg * weight_kg))
    return kcal, protein_g

def macro_split_for_goal(goal: str) -> tuple[int, int, int]:
    # Kthen përqindjet (P, C, Y) sipas qëllimit
    if goal == "Humbje peshe":
        return (30, 40, 30)  # Proteina/ Karbo/ Yndyrna
    if goal == "Shtim muskuj":
        return (30, 50, 20)
    return (25, 50, 25)     # Mbajtje (default)

def macro_targets_grams(total_kcal: int, goal: str, protein_g_from_weight: int) -> tuple[int, int, int]:
    p_pct, c_pct, f_pct = macro_split_for_goal(goal)
    # Llogarit nga %:
    p_kcal = total_kcal * p_pct / 100
    c_kcal = total_kcal * c_pct / 100
    f_kcal = total_kcal * f_pct / 100

    p_g_pct = int(round(p_kcal / 4))
    c_g = int(round(c_kcal / 4))
    f_g = int(round(f_kcal / 9))

    # Përdor maksimumin midis proteina-ve bazuar në peshë dhe atyre nga %
    p_g = max(protein_g_from_weight, p_g_pct)
    return p_g, c_g, f_g

# --- Titulli Kryesor ---
st.title("🍽️ Asistenti i Planifikimit të Ushqimeve me AI")
st.markdown(
    "Krijo një plan ushqimor 7-ditor të shëndetshëm dhe realist, në bazë të kalorive, preferencave dhe përjashtimeve të tua. "
    "Gjenero një listë të blerjeve vetëm me një klikim."
)

# --- Profili & Qëllimi (rekomandim automatik kalorish) ---
with st.expander("🧍‍♂️ Profili & Qëllimi (rekomandim automatik kalorish)", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        gender = st.selectbox("Gjinia", ["Mashkull", "Femër"], index=0)
    with c2:
        age = st.number_input("Mosha", min_value=14, max_value=90, value=28, step=1)
    with c3:
        height_cm = st.number_input("Gjatësia (cm)", min_value=130, max_value=220, value=178, step=1)
    with c4:
        weight_kg = st.number_input("Pesha (kg)", min_value=35.0, max_value=250.0, value=78.0, step=0.5)

    activity = st.selectbox(
        "Aktiviteti ditor",
        ["Në zyrë (pak aktiv)", "Mesatar (3-4x/ javë)", "Sportist (5-6x/ javë)"],
        index=0
    )
    goal = st.radio("Qëllimi", ["Humbje peshe", "Mbajtje", "Shtim muskuj"], index=0, horizontal=True)

    suggested_kcal, suggested_protein = calc_tdee_kcal(gender, age, height_cm, weight_kg, activity, goal)
    # Target makronutrientësh në gramë (bazuar në kcal & qëllim, me proteina >= bazuar në peshë)
    target_p_g, target_c_g, target_f_g = macro_targets_grams(suggested_kcal, goal, suggested_protein)

    use_auto_kcal = st.checkbox("Përdor rekomandimin automatik", value=True)
    st.caption(
        f"Rekomandim: **{suggested_kcal} kcal/ditë** • "
        f"Makronutrientët: **P {target_p_g} g / C {target_c_g} g / Y {target_f_g} g** "
        f"(proteina min. sipas peshës: ~{suggested_protein} g)"
    )

# vlera e parazgjedhur për fushën e kalorive
_default_kcal = suggested_kcal if use_auto_kcal else 2200

col1, col2, col3 = st.columns([1,1,1])
with col1:
    total_kcal = st.number_input("Kaloritë ditore (target)", min_value=1200, max_value=4000, value=_default_kcal, step=50)
with col2:
    pattern = st.text_input("Shpërndarja e kalorive (M/D/D)", value="30/40/30", help="P.sh. 30/40/30 = Mëngjes/Drekë/Darkë")
with col3:
    include_tags = st.multiselect(
        "Etiketa preferencash",
        options=sorted({t for r in recipes for t in r.tags}),
        default=[]
    )

excl = st.text_input("Përjashto përbërës (me presje, p.sh. ‘derr, kërpudha, pikant’)", value="")
exclude_keywords = [x.strip() for x in excl.split(",") if x.strip()]

# --- Kontrollet (miqësore për telefon) ---
with st.expander("⚙️ Funksione shtesë", expanded=False):
    use_ai_subs = st.checkbox("Aktivo Zëvendësimet Inteligjente", value=True, key="subs_main")
    use_ai_expand = st.checkbox("Aktivo Gjenerimin e Recetave të Reja", value=False, key="expand_main")
    localize_albanian = st.checkbox("Përkthe gjithçka në Shqip", value=True, key="sq_main")

    pantry_input = st.text_area(
        "Çfarë ke në shtëpi (shkruaj me presje)",
        placeholder="oriz, vezë, mish pule",
        key="pantry_main"
    )

pantry = [x.strip() for x in pantry_input.split(",") if x.strip()]

st.divider()

# Store the plan in session state to prevent refresh issues
if 'meal_plan' not in st.session_state:
    st.session_state.meal_plan = None

if st.button("Gjenero Planin 7-Ditor", type="primary"):
    plan = make_week_plan(recipes, total_kcal, include_tags, exclude_keywords, pattern)
    st.session_state.meal_plan = plan
    st.success("Plani u krijua me sukses! ✅")

# Display the plan if it exists in session state
if st.session_state.meal_plan:
    plan = st.session_state.meal_plan
    
    # --- Shfaq objektivin ditor (nga Profili) ---
    # Rikalkulo për bazë te total_kcal final (nëse përdoruesi e ndryshon me dorë)
    adj_p_g, adj_c_g, adj_f_g = macro_targets_grams(total_kcal, goal, suggested_protein)
    st.info(
        f"🎯 Objektiv ditor: **{total_kcal} kcal** • "
        f"Makro: **P {adj_p_g} g / C {adj_c_g} g / Y {adj_f_g} g**",
        icon="✅"
    )

    # --- AI Substitutions ---
    if use_ai_subs and pantry:
        st.subheader("✨ Zëvendësime Inteligjente")
        for day in DAYS:
            for meal_type, r in plan[day].items():
                if r:
                    subs = suggest_substitutions(r.ingredients, pantry)
                    emri_vaktit = {"breakfast": "Mëngjes", "lunch": "Drekë", "dinner": "Darkë"}[meal_type]
                    recipe_name = translate_to_albanian(r.name) if localize_albanian else r.name
                    with st.expander(f"Zëvendësime për {day} – {emri_vaktit} ({recipe_name})"):
                        st.markdown(subs)

    # Shfaq planin ushqimor
    for day in DAYS:
        st.subheader(f"📅 {day}")
        meals = plan[day]
        cols = st.columns(3)
        for i, meal_type in enumerate(["breakfast","lunch","dinner"]):
            with cols[i]:
                r = meals[meal_type]
                if r:
                    emri_vaktit = {"breakfast": "Mëngjes", "lunch": "Drekë", "dinner": "Darkë"}[meal_type]
                    
                    # Përkthim i emrit të recetës
                    recipe_name = r.name
                    if localize_albanian:
                        recipe_name = translate_to_albanian(recipe_name)

                    st.markdown(f"**{emri_vaktit}** — *{recipe_name}*")
                    st.caption(f"{r.kcal} kcal • Proteina {r.protein} / Karbo {r.carbs} / Yndyrna {r.fat} • etiketa: {', '.join(r.tags)}")
                    
                    # Përbërësit
                    with st.expander("Përbërësit"):
                        ingredients = r.ingredients
                        if localize_albanian:
                            ingredients = [translate_to_albanian(ing) for ing in ingredients]
                        st.write("\n".join(f"• {x}" for x in ingredients))

                    # Hapat e gatimit
                    with st.expander("Hapat e Gatimit"):
                        steps = r.steps
                        if localize_albanian:
                            steps = [translate_to_albanian(step) for step in steps]
                        for idx, step in enumerate(steps, 1):
                            st.write(f"{idx}. {step}")

                    # Butoni për të ruajtur recetat e gjeneruara nga AI
                    if use_ai_expand and r and "AI" in getattr(r, "tags", []):
                        if st.button(f"💾 Ruaj recetën: {recipe_name}", key=f"save_{day}_{meal_type}"):
                            saved = save_recipe_to_json(r.dict())
                            if saved:
                                st.success("✅ Receta u ruajt në recipes.json!")
                            else:
                                st.error("❌ Nuk u ruajt dot receta.")
                else:
                    emri_vaktit = {"breakfast": "Mëngjes", "lunch": "Drekë", "dinner": "Darkë"}[meal_type]
                    st.warning(f"Nuk u gjet recetë për {emri_vaktit} sipas filtrave.")

    st.divider()
    # Lista e blerjeve
    shopping = build_shopping_list(plan)
    st.subheader("🛒 Lista e Blerjeve")

    rows = []
    for k, v in sorted(shopping.items(), key=lambda x: (-x[1], x[0])):
        item = k
        if localize_albanian:
            item = translate_to_albanian(item)
        rows.append({"Përbërësi": item, "Herë": v})

    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)

    # Butoni për shkarkim liste blerjesh - Fixed encoding
    st.download_button(
        "Shkarko Listën e Blerjeve (CSV)",
        data=df.to_csv(index=False, encoding='utf-8-sig'),
        file_name="lista_blerjeve.csv",
        mime="text/csv",
    )

    # Eksportimi i planit ushqimor
    rows = []
    for day in DAYS:
        for meal_type in ["breakfast","lunch","dinner"]:
            r = plan[day][meal_type]
            recipe_name = r.name if r else ""
            if localize_albanian and r:
                recipe_name = translate_to_albanian(recipe_name)
            rows.append({
                "Dita": day,
                "Vakti": {"breakfast": "Mëngjes", "lunch": "Drekë", "dinner": "Darkë"}[meal_type],
                "Receta": recipe_name,
                "kcal": r.kcal if r else "",
                "Proteina": r.protein if r else "",
                "Karbo": r.carbs if r else "",
                "Yndyrna": r.fat if r else ""
            })
    plan_df = pd.DataFrame(rows)
    st.download_button(
        "Shkarko Planin 7-Ditor (CSV)",
        data=plan_df.to_csv(index=False, encoding='utf-8-sig'),
        file_name="plani_ushqimor.csv",
        mime="text/csv",
    )

else:
    st.info("Vendos preferencat dhe kliko **Gjenero Planin 7-Ditor**.")

st.markdown("---")
st.caption("💡 Këshillë: Shto më shumë receta te `recipes.json` për plane më të pasura. Mund të përdorësh etiketa si `vegetarian`, `budget`, `high-protein`, `gluten-free`, etj.")
