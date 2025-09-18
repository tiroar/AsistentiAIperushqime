import json
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from PIL import Image
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional, Tuple

# Load environment variables from .env file
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")

# Import our custom modules
from database import DatabaseManager
from cloud_compatible import CloudCompatibleDatabaseManager
from auth import AuthManager, render_auth_ui
from planner import Recipe, make_week_plan, build_shopping_list, DAYS
from ai_helpers import suggest_substitutions, expand_recipe_request, translate_to_albanian, save_recipe_to_json
from nutrition_reports import NutritionReportGenerator, render_nutrition_dashboard
from preference_learning import PreferenceLearningSystem, render_preference_learning_ui
from cooking_skills import CookingSkillAdapter, render_cooking_skills_ui
from social_features import SocialFeatures, render_social_features_ui
from analytics_dashboard import AnalyticsDashboard, render_analytics_dashboard
from image_recognition import FoodImageRecognition, render_image_recognition_ui
from herbalife_integration import HerbalifeIntegration, render_herbalife_integration_ui

# Load icon
icon = Image.open("images/icon.png")

# Page configuration
st.set_page_config(
    page_title="Asistenti i Ushqimeve AI",
    page_icon=icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# PWA Meta tags and manifest
st.markdown("""
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#ff6b6b">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Asistenti AI">
<link rel="apple-touch-icon" href="/images/icon-192.png">
""", unsafe_allow_html=True)

# Initialize database and auth
@st.cache_resource
def get_db_manager():
    try:
        # Try to use regular database first (for local development)
        db_manager = DatabaseManager()
        # Test if we can write to the database
        db_manager.save_meal_plan(1, {"test": "data"}, datetime.now())
        return db_manager
    except Exception as e:
        # If database write fails (like on Streamlit Cloud), use cloud-compatible version
        st.warning("⚠️ Using cloud-compatible storage (session state) instead of database")
        return CloudCompatibleDatabaseManager()

@st.cache_resource
def get_auth_manager():
    return AuthManager(get_db_manager())

# Initialize managers
db_manager = get_db_manager()
auth_manager = get_auth_manager()

# Initialize session state
auth_manager.init_session_state()

# Main app logic
def main():
    # Check authentication
    if not st.session_state.is_authenticated:
        render_auth_ui(auth_manager)
        return
    
    # Get current user
    user = auth_manager.get_current_user()
    if not user:
        st.error("Përdoruesi nuk u gjet. Ju lutem identifikohuni përsëri.")
        auth_manager.logout()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.image(icon, width=100)
        st.title(f"Mirë se vini, {user.username}!")
        
        # Guest mode indicator
        if user.auth_provider == "guest":
            st.warning("👤 **Mënyra e Mysafirit** - Të dhënat tuaja nuk do të ruhen përgjithmonë")
            st.info("💡 **Këshillë:** Regjistrohuni për të ruajtur përvojën tuaj përgjithmonë!")
        
        # User info
        if user.auth_provider != "guest":
            st.markdown(f"**Email:** {user.email}")
        st.markdown(f"**Niveli i Gatimit:** {user.cooking_skill.title()}")
        
        # Navigation
        page = st.selectbox(
            "Navigo te:",
            [
                "🍽️ Planifikimi i Ushqimeve",
                "🥤 Herbalife Integration",
                "📊 Paneli i Ushqyerjes", 
                "🍽️ Preferencat e Ushqimit",
                "👨‍🍳 Aftësitë e Gatimit",
                "👥 Veçoritë Sociale",
                "📈 Analitika",
                "📸 Njohja e Ushqimit",
                "⚙️ Cilësimet"
            ]
        )
        
        # Logout button
        if st.button("🚪 Dil"):
            auth_manager.logout()
    
    # Main content area
    if page == "🍽️ Planifikimi i Ushqimeve":
        render_meal_planning_page(user, db_manager)
    elif page == "🥤 Herbalife Integration":
        render_herbalife_integration_ui(user.id, db_manager, lang="sq")
    elif page == "📊 Paneli i Ushqyerjes":
        render_nutrition_dashboard(user.id, db_manager, lang="sq")
    elif page == "🍽️ Preferencat e Ushqimit":
        render_preference_learning_ui(user.id, db_manager, lang="sq")
    elif page == "👨‍🍳 Aftësitë e Gatimit":
        render_cooking_skills_ui(user.id, db_manager, lang="sq")
    elif page == "👥 Veçoritë Sociale":
        render_social_features_ui(user.id, db_manager, lang="sq")
    elif page == "📈 Analitika":
        render_analytics_dashboard(user.id, db_manager, lang="sq")
    elif page == "📸 Njohja e Ushqimit":
        render_image_recognition_ui(user.id, db_manager, lang="sq")
    elif page == "⚙️ Cilësimet":
        render_settings_page(user, db_manager, lang="sq")

def render_meal_planning_page(user, db_manager):
    """Render the main meal planning page with enhanced features"""
    st.title("🍽️ Asistenti i Planifikimit të Ushqimeve me AI")
    st.markdown(
        "Krijo një plan ushqimor 7-ditor të shëndetshëm dhe realist, në bazë të kalorive, preferencave dhe përjashtimeve të tua. "
        "Gjenero një listë të blerjeve vetëm me një klikim."
    )
    
    # Load recipes
    @st.cache_data
    def load_recipes(path: str = "recipes.json", user_path: str = "recipes_user.json"):
        import os, json
        from ai_helpers import enrich_recipe_with_portions
        
        with open(path, "r", encoding="utf-8") as f:
            base = json.load(f)

        user = []
        if os.path.exists(user_path):
            try:
                with open(user_path, "r", encoding="utf-8") as f:
                    user = json.load(f)
            except Exception:
                user = []

        # Merge and de-duplicate by name+meal_type
        seen = set()
        merged = []
        for r in base + user:
            key = (r.get("name","").strip().lower(), r.get("meal_type","").strip().lower())
            if key in seen:
                continue
            seen.add(key)
            
            # Enrich recipe with portion sizes
            enriched_recipe = enrich_recipe_with_portions(r)
            merged.append(enriched_recipe)
            
        return [Recipe(**r) for r in merged]
    
    recipes = load_recipes()
    
    # Enhanced profile section
    with st.expander("🧍‍♂️ Profili & Qëllimi (rekomandim automatik kalorish)", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        
        # Get user profile data
        profile = user.profile_data or {}
        
        with c1:
            gender = st.selectbox("Gjinia", ["Mashkull", "Femër"], 
                                index=0 if profile.get('gender') == 'Mashkull' else 1)
        with c2:
            age = st.number_input("Mosha", min_value=14, max_value=90, 
                                value=profile.get('age', 28), step=1)
        with c3:
            height_cm = st.number_input("Gjatësia (cm)", min_value=130, max_value=220, 
                                      value=profile.get('height', 178), step=1)
        with c4:
            weight_kg = st.number_input("Pesha (kg)", min_value=35.0, max_value=250.0, 
                                      value=profile.get('weight', 78.0), step=0.5)
        
        activity = st.selectbox(
            "Aktiviteti ditor",
            ["Në zyrë (pak aktiv)", "Mesatar (3-4x/ javë)", "Sportist (5-6x/ javë)"],
            index=0
        )
        goal = st.radio("Qëllimi", ["Humbje peshe", "Mbajtje", "Shtim muskuj"], 
                       index=0, horizontal=True)
        
        # Calculate TDEE and macros
        suggested_kcal, suggested_protein = calc_tdee_kcal(gender, age, height_cm, weight_kg, activity, goal)
        target_p_g, target_c_g, target_f_g = macro_targets_grams(suggested_kcal, goal, suggested_protein)
        
        use_auto_kcal = st.checkbox("Përdor rekomandimin automatik", value=True)
        st.caption(
            f"Rekomandim: **{suggested_kcal} kcal/ditë** • "
            f"Makronutrientët: **P {target_p_g} g / C {target_c_g} g / Y {target_f_g} g** "
            f"(proteina min. sipas peshës: ~{suggested_protein} g)"
        )
    
    # Herbalife Integration Checkbox
    st.divider()
    use_herbalife = st.checkbox(
        "🥤 Kombino vaktet me HERBALIFE",
        value=False,
        help="Aktivizo integrimin e produkteve Herbalife në planin tuaj ushqimor për rezultate më të mira"
    )
    
    if use_herbalife:
        st.success("🌿 Herbalife Integration Activated - Your meal plan will include professional Herbalife recommendations")
        
        # Show Herbalife benefits
        with st.expander("💡 Përfitimet e Integrimit Herbalife"):
            st.markdown("""
            **Pse të përdorësh Herbalife?**
            - **Kontroll i Kalorive**: Formula 1 ofron kalori të kontrolluara për humbjen e peshës
            - **Proteinë e Lartë**: 17g proteinë për përzierje për mbështetjen e muskujve
            - **Lëndë Ushqyese**: 21 lëndë ushqyese thelbësore në çdo përzierje
            - **Lehtësi Përdorimi**: Përgatitje e shpejtë dhe e përshtatshme
            - **Rezultate të Provuara**: Produkte të testuara klinikisht për humbjen e peshës
            """)
    
    # Enhanced meal planning controls
    _default_kcal = suggested_kcal if use_auto_kcal else 2200
    
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        total_kcal = st.number_input("Kaloritë ditore (target)", min_value=1200, max_value=4000, 
                                   value=_default_kcal, step=50)
    with col2:
        pattern = st.text_input("Shpërndarja e kalorive (M/D/D)", value="30/40/30", 
                              help="P.sh. 30/40/30 = Mëngjes/Drekë/Darkë")
    with col3:
        include_tags = st.multiselect(
            "Etiketa preferencash",
            options=sorted({t for r in recipes for t in r.tags}),
            default=[]
        )
    
    excl = st.text_input("Përjashto përbërës (me presje, p.sh. 'derr, kërpudha, pikant')", value="")
    exclude_keywords = [x.strip() for x in excl.split(",") if x.strip()]
    
    # Enhanced features
    with st.expander("⚙️ Funksione të Përmirësuara", expanded=False):
        use_ai_subs = st.checkbox("Aktivo Zëvendësimet Inteligjente", value=True, key="subs_main")
        use_ai_expand = st.checkbox("Aktivo Gjenerimin e Recetave të Reja", value=True, key="expand_main")
        localize_albanian = st.checkbox("Përkthe gjithçka në Shqip", value=True, key="sq_main")
        
        pantry_input = st.text_area(
            "Çfarë ke në shtëpi (shkruaj me presje)",
            placeholder="oriz, vezë, mish pule",
            key="pantry_main"
        )
        
        # Cooking skill adaptation
        skill_adapter = CookingSkillAdapter(db_manager)
        cooking_skill = skill_adapter.get_skill_level(user.id)
        st.info(f"🍳 Niveli yt i gatimit: **{cooking_skill.title()}** - Recetat do të përshtaten në përputhje me këtë")
    
    pantry = [x.strip() for x in pantry_input.split(",") if x.strip()]
    
    st.divider()
    
    # Store the plan in session state
    if 'meal_plan' not in st.session_state:
        st.session_state.meal_plan = None
    
    if st.button("Gjenero Planin 7-Ditor", type="primary"):
        # Use preference learning for better recommendations
        preference_system = PreferenceLearningSystem(db_manager)
        user_preferences = preference_system.get_user_preferences(user.id)
        
        # Filter recipes based on preferences
        if user_preferences:
            # This would be implemented to filter recipes based on learned preferences
            pass
        
        # Generate meal plan
        if use_herbalife:
            # Generate Herbalife-integrated meal plan
            herbalife_integration = HerbalifeIntegration(db_manager)
            
            # Create Herbalife recommendations for each day
            herbalife_plan = herbalife_integration.create_herbalife_meal_plan(
                user.id, goal, total_kcal, pattern
            )
            
            # Generate regular meal plan
            plan = make_week_plan(
                recipes, 
                total_kcal, 
                include_tags, 
                exclude_keywords, 
                pattern,
                use_ai_expand=use_ai_expand,
                auto_save_ai=True,
                user_preferences=user_preferences,
                cooking_skill=cooking_skill
            )
            
            # Integrate Herbalife products into the plan
            plan = integrate_herbalife_into_plan(plan, herbalife_plan, goal, db_manager)
            
        else:
            # Generate regular meal plan
            plan = make_week_plan(
                recipes, 
                total_kcal, 
                include_tags, 
                exclude_keywords, 
                pattern,
                use_ai_expand=use_ai_expand,
                auto_save_ai=True,
                user_preferences=user_preferences,
                cooking_skill=cooking_skill
            )
        
        # Adapt recipes for cooking skill level
        for day, meals in plan.items():
            for meal_type, recipe in meals.items():
                if recipe:
                    adapted_recipe = skill_adapter.adapt_recipe_for_skill(recipe.model_dump(), cooking_skill)
                    # Update the recipe with adapted version (only existing fields)
                    valid_fields = ['name', 'meal_type', 'kcal', 'protein', 'carbs', 'fat', 'tags', 'ingredients', 'steps']
                    for key, value in adapted_recipe.items():
                        if key in valid_fields:
                            setattr(recipe, key, value)
        
        st.session_state.meal_plan = plan
        
        # Convert Recipe objects to dictionaries for JSON serialization
        plan_data = {}
        for day, meals in plan.items():
            plan_data[day] = {}
            for meal_type, recipe in meals.items():
                if recipe:
                    plan_data[day][meal_type] = recipe.model_dump()
                else:
                    plan_data[day][meal_type] = None
        
        # Save meal plan to database
        db_manager.save_meal_plan(user.id, plan_data, datetime.now())
        
        # Log analytics event
        db_manager.log_analytics_event(user.id, 'meal_plan_generated', {
            'total_kcal': total_kcal,
            'include_tags': include_tags,
            'exclude_keywords': exclude_keywords
        })
        
        # Check for achievements
        social = SocialFeatures(db_manager)
        social.check_and_award_achievements(user.id, 'meal_plan_generated')
        
        st.success("Plani u krijua me sukses! ✅")
    
    # Display the plan
    if st.session_state.meal_plan:
        plan = st.session_state.meal_plan
        
        # Show daily objective
        adj_p_g, adj_c_g, adj_f_g = macro_targets_grams(total_kcal, goal, suggested_protein)
        st.info(
            f"🎯 Objektiv ditor: **{total_kcal} kcal** • "
            f"Makro: **P {adj_p_g} g / C {adj_c_g} g / Y {adj_f_g} g**",
            icon="✅"
        )
        
        # AI Substitutions
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
        
        # Show plan
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
                            
                            # Show Herbalife products if integrated
                            if hasattr(r, 'herbalife_products') and r.herbalife_products:
                                st.markdown("**🥤 Produktet Herbalife:**")
                                for product in r.herbalife_products:
                                    st.write(f"• {product.albanian_name} ({product.serving_size})")
                                    st.caption(f"   {product.calories} kcal, {product.protein}g proteinë")

                        # Hapat e gatimit
                        with st.expander("Hapat e Gatimit"):
                            steps = r.steps
                            if localize_albanian:
                                steps = [translate_to_albanian(step) for step in steps]
                            for idx, step in enumerate(steps, 1):
                                st.write(f"{idx}. {step}")
                            
                            # Show Herbalife preparation steps
                            if hasattr(r, 'herbalife_products') and r.herbalife_products:
                                st.markdown("**🥤 Përgatitja e Produkteve Herbalife:**")
                                for product in r.herbalife_products:
                                    st.write(f"• {product.albanian_name}: {product.preparation}")
                                    if product.benefits:
                                        st.caption(f"   Përfitimet: {', '.join(product.benefits)}")
                        
                        # Cooking skill tips
                        if hasattr(r, 'beginner_tips') and r.beginner_tips:
                            with st.expander("Këshilla Gatimi"):
                                for tip in r.beginner_tips:
                                    st.write(f"💡 {tip}")
                        
                        # Save AI-generated recipes
                        if use_ai_expand and r and "AI" in getattr(r, "tags", []):
                            if st.button(f"💾 Ruaj recetën: {recipe_name}", key=f"save_{day}_{meal_type}"):
                                saved = save_recipe_to_json(r.model_dump())
                                if saved:
                                    st.success("✅ Receta u ruajt në recipes.json!")
                                else:
                                    st.error("❌ Nuk u ruajt dot receta.")
                    else:
                        emri_vaktit = {"breakfast": "Mëngjes", "lunch": "Drekë", "dinner": "Darkë"}[meal_type]
                        st.warning(f"Nuk u gjet recetë për {emri_vaktit} sipas filtrave.")
        
        st.divider()
        
        # Shopping list
        shopping = build_shopping_list(plan)
        
        # Add Herbalife products to shopping list if integrated
        if use_herbalife:
            herbalife_integration = HerbalifeIntegration(db_manager)
            herbalife_plan = herbalife_integration.create_herbalife_meal_plan(user.id, goal, total_kcal, pattern)
            herbalife_shopping = herbalife_integration.get_herbalife_shopping_list(herbalife_plan)
            
            # Merge Herbalife products into shopping list
            for product, count in herbalife_shopping.items():
                shopping[f"🥤 {product}"] = count
        
        st.subheader("🛒 Lista e Blerjeve")
        
        rows = []
        for k, v in sorted(shopping.items(), key=lambda x: (-x[1], x[0])):
            item = k
            if localize_albanian and not item.startswith("🥤"):
                item = translate_to_albanian(item)
            rows.append({"Përbërësi": item, "Herë": v})
        
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch", hide_index=True)
        
        # Show Herbalife nutrition summary if integrated
        if use_herbalife:
            st.subheader("🥤 Përmbledhje Nutritive Herbalife")
            herbalife_nutrition = herbalife_integration.calculate_herbalife_nutrition(herbalife_plan)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Kalori Herbalife", herbalife_nutrition['calories'])
            with col2:
                st.metric("Proteina (g)", herbalife_nutrition['protein'])
            with col3:
                st.metric("Karbohidratet (g)", herbalife_nutrition['carbs'])
            with col4:
                st.metric("Yndyrnat (g)", herbalife_nutrition['fat'])
        
        # Download buttons
        st.download_button(
            "Shkarko Listën e Blerjeve (CSV)",
            data=df.to_csv(index=False, encoding='utf-8-sig'),
            file_name="lista_blerjeve.csv",
            mime="text/csv",
        )
        
        # Export weekly plan as CSV
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
        
        # Generate nutrition report
        if st.button("📊 Gjenero Raportin Javor të Ushqyerjes"):
            with st.spinner("Po gjenerohet raporti i ushqyerjes..."):
                report_generator = NutritionReportGenerator(db_manager)
                
                # Get recent meal plans for the report
                recent_plans = db_manager.get_meal_plans(user.id, limit=1)
                
                if recent_plans:
                    report = report_generator.generate_weekly_report(
                        user.id, 
                        recent_plans[0]['week_start'], 
                        recent_plans
                    )
                    
                    if report:
                        st.success("✅ Raporti i ushqyerjes u gjenerua! Shkoni te '📊 Paneli i Ushqyerjes' në menunë anësore për ta parë.")
                    else:
                        st.error("❌ Dështoi gjenerimi i raportit të ushqyerjes")
                else:
                    st.error("Nuk u gjet plan ushqimor për të gjeneruar raportin")
    
    else:
        st.info("Vendos preferencat dhe kliko **Gjenero Planin 7-Ditor**.")
    
    st.markdown("---")
    st.caption("💡 Këshillë: Shto më shumë receta te `recipes.json` për plane më të pasura. Mund të përdorësh etiketa si `vegetarian`, `budget`, `high-protein`, `gluten-free`, etj.")

def render_settings_page(user, db_manager, lang="sq"):
    """Render settings page"""
    st.title("⚙️ Cilësimet")
    
    # User profile settings
    st.subheader("Cilësimet e Profilit")
    
    with st.form("profile_settings"):
        new_username = st.text_input("Emri i Përdoruesit", value=user.username)
        new_email = st.text_input("Email", value=user.email)
        
        # Update profile data
        profile = user.profile_data.copy()
        
        col1, col2 = st.columns(2)
        with col1:
            profile['age'] = st.number_input("Mosha", value=profile.get('age', 28), min_value=14, max_value=90)
            profile['height'] = st.number_input("Gjatësia (cm)", value=profile.get('height', 178), min_value=130, max_value=220)
        with col2:
            profile['weight'] = st.number_input("Pesha (kg)", value=profile.get('weight', 78.0), min_value=35.0, max_value=250.0)
            profile['gender'] = st.selectbox("Gjinia", ["Mashkull", "Femër"], index=0 if profile.get('gender') == 'Mashkull' else 1)
        
        if st.form_submit_button("Përditëso Profilin"):
            # Update user profile in database
            conn = db_manager.db_path
            import sqlite3
            conn = sqlite3.connect(conn)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET username = ?, email = ?, profile_data = ?
                WHERE id = ?
            ''', (new_username, new_email, json.dumps(profile), user.id))
            
            conn.commit()
            conn.close()
            
            st.success("Profili u përditësua me sukses!")
            st.rerun()
    
    # Preferences settings
    st.subheader("Preferencat")
    
    preferences = user.preferences.copy()
    
    with st.form("preferences_settings"):
        dietary_restrictions = st.multiselect(
            "Kufizimet Dietike",
            ["Vegetarian", "Vegan", "Pa Gluten", "Pa Laktosë", "Pa Arrë", "Keto", "Paleo"],
            default=preferences.get('dietary_restrictions', [])
        )
        
        favorite_cuisines = st.multiselect(
            "Kuzhinat e Preferuara",
            ["Italiane", "Aziatike", "Mesdhetare", "Meksikane", "Amerikane", "Indiane", "Frëngjishte", "Tajlandeze"],
            default=preferences.get('favorite_cuisines', [])
        )
        
        disliked_foods = st.text_area(
            "Ushqimet që nuk i pëlqen (një për rresht)",
            value="\n".join(preferences.get('disliked_foods', [])),
            help="Shkruaj ushqimet që nuk i pëlqen, një për rresht"
        )
        
        if st.form_submit_button("Përditëso Preferencat"):
            preferences['dietary_restrictions'] = dietary_restrictions
            preferences['favorite_cuisines'] = favorite_cuisines
            preferences['disliked_foods'] = [food.strip() for food in disliked_foods.split('\n') if food.strip()]
            
            # Update preferences in database
            conn = db_manager.db_path
            import sqlite3
            conn = sqlite3.connect(conn)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET preferences = ? WHERE id = ?
            ''', (json.dumps(preferences), user.id))
            
            conn.commit()
            conn.close()
            
            st.success("Preferencat u përditësuan me sukses!")
            st.rerun()
    
    # Account settings
    st.subheader("Cilësimet e Llogarisë")
    
    # Password change section
    if not st.session_state.get('show_password_change', False):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Ndrysho Fjalëkalimin"):
                st.session_state.show_password_change = True
                st.rerun()
        
        with col2:
            if st.button("Fshi Llogarinë", type="secondary"):
                st.session_state.show_delete_account = True
                st.rerun()
    
    # Password change form
    if st.session_state.get('show_password_change', False):
        st.subheader("Ndrysho Fjalëkalimin")
        
        with st.form("change_password_form"):
            current_password = st.text_input("Fjalëkalimi Aktual", type="password")
            new_password = st.text_input("Fjalëkalimi i Ri", type="password")
            confirm_password = st.text_input("Konfirmo Fjalëkalimin e Ri", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Ndrysho Fjalëkalimin", type="primary"):
                    # Validate inputs
                    if not current_password or not new_password or not confirm_password:
                        st.error("Ju lutem plotësoni të gjitha fushat")
                    elif new_password != confirm_password:
                        st.error("Fjalëkalimet e reja nuk përputhen")
                    elif len(new_password) < 6:
                        st.error("Fjalëkalimi i ri duhet të ketë të paktën 6 karaktere")
                    else:
                        # Verify current password by getting it from database
                        import hashlib
                        current_hash = hashlib.sha256(current_password.encode()).hexdigest()
                        
                        conn = db_manager.db_path
                        import sqlite3
                        conn = sqlite3.connect(conn)
                        cursor = conn.cursor()
                        
                        # Get current password hash from database
                        cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user.id,))
                        stored_hash = cursor.fetchone()[0]
                        
                        if current_hash != stored_hash:
                            st.error("Fjalëkalimi aktual është i gabuar")
                        else:
                            # Update password
                            new_hash = hashlib.sha256(new_password.encode()).hexdigest()
                            
                            cursor.execute('''
                                UPDATE users SET password_hash = ? WHERE id = ?
                            ''', (new_hash, user.id))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success("Fjalëkalimi u ndryshua me sukses!")
                            st.session_state.show_password_change = False
                            st.rerun()
            
            with col2:
                if st.form_submit_button("Anulo"):
                    st.session_state.show_password_change = False
                    st.rerun()
    
    # Account deletion confirmation
    if st.session_state.get('show_delete_account', False):
        st.subheader("Fshi Llogarinë")
        st.warning("⚠️ Kjo veprim do të fshijë përgjithmonë llogarinë tuaj dhe të gjitha të dhënat e lidhura!")
        
        with st.form("delete_account_form"):
            confirm_text = st.text_input(
                "Shkruaj 'FSHI' për të konfirmuar fshirjen e llogarisë",
                placeholder="FSHI"
            )
            password_confirm = st.text_input("Fjalëkalimi për konfirmim", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Fshi Llogarinë", type="secondary"):
                    if confirm_text != "FSHI":
                        st.error("Ju lutem shkruani 'FSHI' për të konfirmuar")
                    elif not password_confirm:
                        st.error("Ju lutem shkruani fjalëkalimin për konfirmim")
                    else:
                        # Verify password by getting it from database
                        import hashlib
                        password_hash = hashlib.sha256(password_confirm.encode()).hexdigest()
                        
                        conn = db_manager.db_path
                        import sqlite3
                        conn = sqlite3.connect(conn)
                        cursor = conn.cursor()
                        
                        # Get password hash from database
                        cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user.id,))
                        stored_hash = cursor.fetchone()[0]
                        
                        if password_hash != stored_hash:
                            st.error("Fjalëkalimi është i gabuar")
                            conn.close()
                        else:
                            # Delete account and all related data
                            
                            # Delete all user data
                            cursor.execute('DELETE FROM user_profiles WHERE user_id = ?', (user.id,))
                            cursor.execute('DELETE FROM user_preferences WHERE user_id = ?', (user.id,))
                            cursor.execute('DELETE FROM nutrition_reports WHERE user_id = ?', (user.id,))
                            cursor.execute('DELETE FROM meal_plans WHERE user_id = ?', (user.id,))
                            cursor.execute('DELETE FROM user_achievements WHERE user_id = ?', (user.id,))
                            cursor.execute('DELETE FROM user_challenges WHERE user_id = ?', (user.id,))
                            cursor.execute('DELETE FROM food_recognition_logs WHERE user_id = ?', (user.id,))
                            cursor.execute('DELETE FROM analytics_events WHERE user_id = ?', (user.id,))
                            cursor.execute('DELETE FROM users WHERE id = ?', (user.id,))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success("Llogaria u fshi me sukses!")
                            st.session_state.show_delete_account = False
                            st.session_state.authenticated = False
                            st.session_state.user = None
                            st.rerun()
            
            with col2:
                if st.form_submit_button("Anulo"):
                    st.session_state.show_delete_account = False
                    st.rerun()

# Helper functions (from original app)
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

def integrate_herbalife_into_plan(regular_plan: Dict, herbalife_plan: Dict, goal: str, db_manager) -> Dict:
    """Integrate Herbalife products into the regular meal plan"""
    from herbalife_integration import HerbalifeIntegration
    from planner import Recipe
    
    # Pass db_manager (can be None for cloud compatibility)
    herbalife = HerbalifeIntegration(db_manager)
    
    integrated_plan = {}
    
    for day in regular_plan.keys():
        day_plan = {}
        
        for meal_type in ["breakfast", "lunch", "dinner"]:
            regular_recipe = regular_plan[day].get(meal_type)
            
            if meal_type in herbalife_plan:
                herbalife_meal = herbalife_plan[meal_type]
                
                # Create integrated meal
                if regular_recipe:
                    # Combine regular recipe with Herbalife
                    integrated_recipe_data = {
                        "name": f"{regular_recipe.name} + {herbalife_meal['primary'].albanian_name}",
                        "meal_type": meal_type,
                        "kcal": regular_recipe.kcal + herbalife_meal['total_calories'],
                        "protein": regular_recipe.protein + herbalife_meal['primary'].protein,
                        "carbs": regular_recipe.carbs + herbalife_meal['primary'].carbs,
                        "fat": regular_recipe.fat + herbalife_meal['primary'].fat,
                        "tags": regular_recipe.tags + ["herbalife", "integrated"],
                        "ingredients": regular_recipe.ingredients + [
                            f"🥤 {herbalife_meal['primary'].albanian_name} ({herbalife_meal['primary'].serving_size})"
                        ],
                        "steps": regular_recipe.steps + [
                            f"Përgatit {herbalife_meal['primary'].albanian_name}: {herbalife_meal['primary'].preparation}",
                            f"💡 {herbalife_meal['albanian_recommendation']}"
                        ]
                    }
                    
                    # Create Recipe object
                    integrated_recipe = Recipe(**integrated_recipe_data)
                    
                    day_plan[meal_type] = integrated_recipe
                else:
                    # Use only Herbalife if no regular recipe
                    herbalife_recipe_data = {
                        "name": f"Herbalife {herbalife_meal['primary'].albanian_name}",
                        "meal_type": meal_type,
                        "kcal": herbalife_meal['total_calories'],
                        "protein": herbalife_meal['primary'].protein,
                        "carbs": herbalife_meal['primary'].carbs,
                        "fat": herbalife_meal['primary'].fat,
                        "tags": ["herbalife", "meal_replacement"],
                        "ingredients": [
                            f"🥤 {herbalife_meal['primary'].albanian_name} ({herbalife_meal['primary'].serving_size})"
                        ],
                        "steps": [
                            f"Përgatit {herbalife_meal['primary'].albanian_name}: {herbalife_meal['primary'].preparation}",
                            f"💡 {herbalife_meal['albanian_recommendation']}"
                        ]
                    }
                    
                    # Create Recipe object
                    herbalife_recipe = Recipe(**herbalife_recipe_data)
                    
                    day_plan[meal_type] = herbalife_recipe
            else:
                day_plan[meal_type] = regular_recipe
        
        integrated_plan[day] = day_plan
    
    return integrated_plan

if __name__ == "__main__":
    main()