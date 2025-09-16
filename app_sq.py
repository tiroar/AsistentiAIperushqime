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

# --- Titulli Kryesor ---
st.title("🍽️ Asistenti i Planifikimit të Ushqimeve me AI")
st.markdown(
    "Krijo një plan ushqimor 7-ditor të shëndetshëm dhe realist, në bazë të kalorive, preferencave dhe përjashtimeve të tua. "
    "Gjenero një listë të blerjeve vetëm me një klikim."
)

col1, col2, col3 = st.columns([1,1,1])
with col1:
    total_kcal = st.number_input("Kaloritë ditore (target)", min_value=1200, max_value=4000, value=2200, step=50)
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
if st.button("Gjenero Planin 7-Ditor", type="primary"):
    plan = make_week_plan(recipes, total_kcal, include_tags, exclude_keywords, pattern)
    st.success("Plani u krijua me sukses! ✅")

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

    # Butoni për shkarkim liste blerjesh
    st.download_button(
        "Shkarko Listën e Blerjeve (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
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
        data=plan_df.to_csv(index=False).encode("utf-8"),
        file_name="plani_ushqimor.csv",
        mime="text/csv",
    )

else:
    st.info("Vendos preferencat dhe kliko **Gjenero Planin 7-Ditor**.")

st.markdown("---")
st.caption("💡 Këshillë: Shto më shumë receta te `recipes.json` për plane më të pasura. Mund të përdorësh etiketa si `vegetarian`, `budget`, `high-protein`, `gluten-free`, etj.")
