import streamlit as st
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from database import DatabaseManager
import random

class HerbalifeProduct:
    """Herbalife product data model"""
    def __init__(self, name: str, product_type: str, calories: int, protein: float, 
                 carbs: float, fat: float, serving_size: str, meal_timing: List[str],
                 preparation: str, benefits: List[str], albanian_name: str = None):
        self.name = name
        self.product_type = product_type  # 'shake', 'tea', 'supplement', 'snack'
        self.calories = calories
        self.protein = protein
        self.carbs = carbs
        self.fat = fat
        self.serving_size = serving_size
        self.meal_timing = meal_timing  # ['breakfast', 'lunch', 'dinner', 'snack']
        self.preparation = preparation
        self.benefits = benefits
        self.albanian_name = albanian_name or name

class HerbalifeIntegration:
    """Professional Herbalife integration system"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.products = self._initialize_herbalife_products()
    
    def _initialize_herbalife_products(self) -> Dict[str, HerbalifeProduct]:
        """Initialize comprehensive Herbalife product database"""
        products = {}
        
        # Formula 1 Nutritional Shake Mix - Core product
        products['formula1_vanilla'] = HerbalifeProduct(
            name="Formula 1 Nutritional Shake Mix - Vanilla",
            albanian_name="Formula 1 Përzierje Nutritive - Vanilje",
            product_type="shake",
            calories=170,
            protein=17.0,
            carbs=13.0,
            fat=2.0,
            serving_size="2 scoops + 250ml milk",
            meal_timing=["breakfast", "lunch", "dinner"],
            preparation="Mix 2 scoops with 250ml nonfat milk or soymilk. Blend or shake well.",
            benefits=["Meal replacement", "High protein", "21 essential nutrients", "Weight management"]
        )
        
        products['formula1_chocolate'] = HerbalifeProduct(
            name="Formula 1 Nutritional Shake Mix - Chocolate",
            albanian_name="Formula 1 Përzierje Nutritive - Çokollatë",
            product_type="shake",
            calories=170,
            protein=17.0,
            carbs=13.0,
            fat=2.0,
            serving_size="2 scoops + 250ml milk",
            meal_timing=["breakfast", "lunch", "dinner"],
            preparation="Mix 2 scoops with 250ml nonfat milk or soymilk. Blend or shake well.",
            benefits=["Meal replacement", "High protein", "21 essential nutrients", "Weight management"]
        )
        
        # Personalized Protein Powder
        products['protein_powder'] = HerbalifeProduct(
            name="Personalized Protein Powder",
            albanian_name="Pluhur Proteini i Personalizuar",
            product_type="supplement",
            calories=20,
            protein=5.0,
            carbs=0.0,
            fat=0.0,
            serving_size="1 tablespoon",
            meal_timing=["breakfast", "lunch", "dinner", "snack"],
            preparation="Add to shakes, smoothies, or meals to increase protein content.",
            benefits=["Additional protein", "Muscle support", "Versatile usage"]
        )
        
        # Herbal Tea Concentrate
        products['herbal_tea'] = HerbalifeProduct(
            name="Herbal Tea Concentrate",
            albanian_name="Koncentrat Çaji Bimor",
            product_type="tea",
            calories=5,
            protein=0.0,
            carbs=1.0,
            fat=0.0,
            serving_size="1 teaspoon + 250ml water",
            meal_timing=["breakfast", "snack"],
            preparation="Mix 1 teaspoon with 250ml hot water. Steep for 3-5 minutes.",
            benefits=["Metabolism support", "Antioxidants", "Natural energy"]
        )
        
        # Afresh Energy Drink
        products['afresh_energy'] = HerbalifeProduct(
            name="Afresh Energy Drink",
            albanian_name="Pije Energjie Afresh",
            product_type="tea",
            calories=15,
            protein=0.0,
            carbs=4.0,
            fat=0.0,
            serving_size="1 sachet + 250ml water",
            meal_timing=["breakfast", "snack"],
            preparation="Mix 1 sachet with 250ml cold water. Stir well.",
            benefits=["Natural energy", "Caffeine", "Tulsi extract", "Low calorie"]
        )
        
        # Herbal Aloe Concentrate
        products['aloe_concentrate'] = HerbalifeProduct(
            name="Herbal Aloe Concentrate",
            albanian_name="Koncentrat Aloe Bimor",
            product_type="supplement",
            calories=10,
            protein=0.0,
            carbs=2.0,
            fat=0.0,
            serving_size="2 capfuls + 250ml water",
            meal_timing=["breakfast", "lunch", "dinner"],
            preparation="Mix 2 capfuls with 250ml water. Drink throughout the day.",
            benefits=["Digestive health", "Hydration", "Nutrient absorption"]
        )
        
        # Protein Bars
        products['protein_bar'] = HerbalifeProduct(
            name="Protein Bar",
            albanian_name="Biskotë Proteini",
            product_type="snack",
            calories=140,
            protein=10.0,
            carbs=15.0,
            fat=4.0,
            serving_size="1 bar",
            meal_timing=["snack"],
            preparation="Ready to eat. Store in cool, dry place.",
            benefits=["Convenient protein", "Portable snack", "Satisfying"]
        )
        
        return products
    
    def get_herbalife_recommendations(self, user_profile: Dict, goal: str, 
                                    meal_type: str, target_calories: int) -> List[HerbalifeProduct]:
        """Get professional Herbalife recommendations based on user profile and goals"""
        recommendations = []
        
        # Weight loss recommendations
        if goal == "Humbje peshe" or goal == "Weight Loss":
            if meal_type == "breakfast":
                # Formula 1 shake for breakfast (most important meal for weight loss)
                recommendations.append(self.products['formula1_vanilla'])
                recommendations.append(self.products['herbal_tea'])
            elif meal_type == "lunch":
                # Formula 1 shake for lunch (controlled calories)
                recommendations.append(self.products['formula1_chocolate'])
                recommendations.append(self.products['aloe_concentrate'])
            elif meal_type == "dinner":
                # Light dinner with protein powder
                recommendations.append(self.products['protein_powder'])
            else:  # snack
                recommendations.append(self.products['protein_bar'])
                recommendations.append(self.products['afresh_energy'])
        
        # Weight maintenance recommendations
        elif goal == "Mbajtje" or goal == "Maintenance":
            if meal_type == "breakfast":
                recommendations.append(self.products['formula1_vanilla'])
                recommendations.append(self.products['herbal_tea'])
            elif meal_type == "lunch":
                # Regular lunch with Herbalife supplement
                recommendations.append(self.products['protein_powder'])
            elif meal_type == "dinner":
                # Regular dinner
                recommendations.append(self.products['aloe_concentrate'])
            else:  # snack
                recommendations.append(self.products['protein_bar'])
        
        # Muscle building recommendations
        elif goal == "Shtim muskuj" or goal == "Muscle Building":
            if meal_type == "breakfast":
                recommendations.append(self.products['formula1_chocolate'])
                recommendations.append(self.products['protein_powder'])
            elif meal_type == "lunch":
                recommendations.append(self.products['formula1_vanilla'])
                recommendations.append(self.products['protein_powder'])
            elif meal_type == "dinner":
                recommendations.append(self.products['protein_powder'])
            else:  # snack
                recommendations.append(self.products['protein_bar'])
                recommendations.append(self.products['protein_powder'])
        
        # Filter by calorie target
        filtered_recommendations = []
        for product in recommendations:
            if product.calories <= target_calories * 0.8:  # Leave room for other foods
                filtered_recommendations.append(product)
        
        return filtered_recommendations[:2]  # Return top 2 recommendations
    
    def create_herbalife_meal_plan(self, user_id: int, goal: str, total_kcal: int, 
                                 pattern: str = "30/40/30") -> Dict:
        """Create a comprehensive Herbalife-integrated meal plan"""
        
        # Calculate calorie distribution
        try:
            b, l, d = [int(x) for x in pattern.split("/")]
            factor = total_kcal / (b + l + d)
            calorie_split = {
                "breakfast": int(round(b * factor)),
                "lunch": int(round(l * factor)),
                "dinner": int(round(d * factor)),
            }
        except:
            calorie_split = {"breakfast": int(total_kcal * 0.3), 
                           "lunch": int(total_kcal * 0.4), 
                           "dinner": int(total_kcal * 0.3)}
        
        # Get user profile
        user = self.db.get_user_by_id(user_id)
        profile = user.profile_data if user else {}
        
        # Create Herbalife meal plan
        herbalife_plan = {
            "breakfast": self._create_herbalife_breakfast(goal, calorie_split["breakfast"]),
            "lunch": self._create_herbalife_lunch(goal, calorie_split["lunch"]),
            "dinner": self._create_herbalife_dinner(goal, calorie_split["dinner"]),
            "snacks": self._create_herbalife_snacks(goal, total_kcal - sum(calorie_split.values()))
        }
        
        return herbalife_plan
    
    def _create_herbalife_breakfast(self, goal: str, target_calories: int) -> Dict:
        """Create Herbalife breakfast recommendation"""
        if goal in ["Humbje peshe", "Weight Loss"]:
            return {
                "primary": self.products['formula1_vanilla'],
                "supplement": self.products['herbal_tea'],
                "total_calories": self.products['formula1_vanilla'].calories + self.products['herbal_tea'].calories,
                "recommendation": "Formula 1 shake for breakfast provides controlled calories and essential nutrients. Herbal tea supports metabolism.",
                "albanian_recommendation": "Formula 1 për mëngjes ofron kalori të kontrolluara dhe lëndë ushqyese thelbësore. Çaji bimor mbështet metabolizmin."
            }
        else:
            return {
                "primary": self.products['formula1_chocolate'],
                "supplement": self.products['herbal_tea'],
                "total_calories": self.products['formula1_chocolate'].calories + self.products['herbal_tea'].calories,
                "recommendation": "Formula 1 shake provides a nutritious start to your day with high-quality protein.",
                "albanian_recommendation": "Formula 1 ofron një fillim ushqyes për ditën tuaj me proteinë cilësore të lartë."
            }
    
    def _create_herbalife_lunch(self, goal: str, target_calories: int) -> Dict:
        """Create Herbalife lunch recommendation"""
        if goal in ["Humbje peshe", "Weight Loss"]:
            return {
                "primary": self.products['formula1_chocolate'],
                "supplement": self.products['aloe_concentrate'],
                "total_calories": self.products['formula1_chocolate'].calories + self.products['aloe_concentrate'].calories,
                "recommendation": "Formula 1 shake for lunch helps maintain calorie control while providing essential nutrients.",
                "albanian_recommendation": "Formula 1 për drekë ndihmon në kontrollin e kalorive duke ofruar lëndë ushqyese thelbësore."
            }
        else:
            return {
                "primary": self.products['protein_powder'],
                "supplement": self.products['aloe_concentrate'],
                "total_calories": self.products['protein_powder'].calories + self.products['aloe_concentrate'].calories,
                "recommendation": "Add protein powder to your regular lunch for extra protein. Aloe supports digestive health.",
                "albanian_recommendation": "Shtoni pluhurin e proteinës në drekën tuaj të rregullt për proteinë shtesë. Aloe mbështet shëndetin tretësor."
            }
    
    def _create_herbalife_dinner(self, goal: str, target_calories: int) -> Dict:
        """Create Herbalife dinner recommendation"""
        if goal in ["Shtim muskuj", "Muscle Building"]:
            return {
                "primary": self.products['protein_powder'],
                "supplement": self.products['aloe_concentrate'],
                "total_calories": self.products['protein_powder'].calories + self.products['aloe_concentrate'].calories,
                "recommendation": "Protein powder with dinner supports muscle recovery. Aloe aids digestion.",
                "albanian_recommendation": "Pluhuri i proteinës me darkën mbështet rikuperimin e muskujve. Aloe ndihmon tretjen."
            }
        else:
            return {
                "primary": self.products['aloe_concentrate'],
                "supplement": None,
                "total_calories": self.products['aloe_concentrate'].calories,
                "recommendation": "Aloe concentrate supports digestive health and nutrient absorption.",
                "albanian_recommendation": "Koncentrati i aloe mbështet shëndetin tretësor dhe thithjen e lëndëve ushqyese."
            }
    
    def _create_herbalife_snacks(self, goal: str, target_calories: int) -> Dict:
        """Create Herbalife snack recommendations"""
        snacks = []
        
        if goal in ["Humbje peshe", "Weight Loss"]:
            snacks.append(self.products['protein_bar'])
            snacks.append(self.products['afresh_energy'])
        else:
            snacks.append(self.products['protein_bar'])
            snacks.append(self.products['herbal_tea'])
        
        return {
            "snacks": snacks,
            "total_calories": sum(s.calories for s in snacks),
            "recommendation": "Herbalife snacks provide convenient nutrition between meals.",
            "albanian_recommendation": "Ushqimet e lehta Herbalife ofrojnë ushqim të përshtatshëm midis vakteve."
        }
    
    def get_herbalife_shopping_list(self, herbalife_plan: Dict) -> Dict[str, int]:
        """Generate Herbalife shopping list"""
        shopping_list = {}
        
        for meal_type, meal_data in herbalife_plan.items():
            if meal_type == "snacks":
                for snack in meal_data["snacks"]:
                    product_name = snack.albanian_name
                    shopping_list[product_name] = shopping_list.get(product_name, 0) + 1
            else:
                if meal_data.get("primary"):
                    product_name = meal_data["primary"].albanian_name
                    shopping_list[product_name] = shopping_list.get(product_name, 0) + 1
                
                if meal_data.get("supplement"):
                    product_name = meal_data["supplement"].albanian_name
                    shopping_list[product_name] = shopping_list.get(product_name, 0) + 1
        
        return shopping_list
    
    def calculate_herbalife_nutrition(self, herbalife_plan: Dict) -> Dict:
        """Calculate total nutrition from Herbalife plan"""
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        for meal_type, meal_data in herbalife_plan.items():
            if meal_type == "snacks":
                for snack in meal_data["snacks"]:
                    total_calories += snack.calories
                    total_protein += snack.protein
                    total_carbs += snack.carbs
                    total_fat += snack.fat
            else:
                if meal_data.get("primary"):
                    product = meal_data["primary"]
                    total_calories += product.calories
                    total_protein += product.protein
                    total_carbs += product.carbs
                    total_fat += product.fat
                
                if meal_data.get("supplement"):
                    product = meal_data["supplement"]
                    total_calories += product.calories
                    total_protein += product.protein
                    total_carbs += product.carbs
                    total_fat += product.fat
        
        return {
            "calories": total_calories,
            "protein": round(total_protein, 1),
            "carbs": round(total_carbs, 1),
            "fat": round(total_fat, 1)
        }

def render_herbalife_integration_ui(user_id: int, db_manager: DatabaseManager, lang: str = "sq"):
    """Render Herbalife integration UI"""
    st.title("🥤 Integrimi Herbalife")
    
    herbalife = HerbalifeIntegration(db_manager)
    
    # Herbalife integration checkbox
    use_herbalife = st.checkbox(
        "Kombino vaktet me HERBALIFE",
        value=False,
        help="Aktivizo integrimin e produkteve Herbalife në planin tuaj ushqimor"
    )
    
    if use_herbalife:
        st.info("🌿 Herbalife Integration Activated - Your meal plan will include professional Herbalife recommendations")
        
        # Get user profile for recommendations
        user = db_manager.get_user_by_id(user_id)
        if user:
            profile = user.profile_data
            goal = profile.get('goal', 'Humbje peshe')
            
            # Display Herbalife recommendations
            st.subheader("💡 Rekomandimet Herbalife për Ju")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Mëngjes**")
                breakfast_rec = herbalife.get_herbalife_recommendations(profile, goal, "breakfast", 400)
                for product in breakfast_rec:
                    st.write(f"• {product.albanian_name}")
                    st.caption(f"{product.calories} kcal, {product.protein}g proteinë")
            
            with col2:
                st.markdown("**Drekë**")
                lunch_rec = herbalife.get_herbalife_recommendations(profile, goal, "lunch", 500)
                for product in lunch_rec:
                    st.write(f"• {product.albanian_name}")
                    st.caption(f"{product.calories} kcal, {product.protein}g proteinë")
            
            # Herbalife product information
            st.subheader("📋 Informacione për Produktet Herbalife")
            
            with st.expander("Formula 1 Nutritional Shake Mix"):
                st.markdown("""
                **Përshkrimi**: Përzierje nutritive për zëvendësimin e vakteve
                **Përdorimi**: 2 lugë + 250ml qumësht
                **Përfitimet**: 
                - 21 lëndë ushqyese thelbësore
                - Proteinë e lartë (17g)
                - Kontroll i kalorive
                - Përshtatshëm për humbjen e peshës
                """)
            
            with st.expander("Personalized Protein Powder"):
                st.markdown("""
                **Përshkrimi**: Pluhur proteini për shtim në ushqime
                **Përdorimi**: 1 lugë në ushqime ose pije
                **Përfitimet**:
                - Proteinë shtesë (5g për lugë)
                - Përdorim i larmishëm
                - Mbështet rritjen e muskujve
                """)
            
            with st.expander("Herbal Tea Concentrate"):
                st.markdown("""
                **Përshkrimi**: Çaj bimor për mbështetjen e metabolizmit
                **Përdorimi**: 1 lugë çaji + 250ml ujë të nxehtë
                **Përfitimet**:
                - Mbështet metabolizmin
                - Antioksidantë
                - Energji natyrore
                """)
        
        return True
    else:
        st.info("Herbalife integration is disabled. Enable it to get professional Herbalife recommendations in your meal plan.")
        return False

