import streamlit as st
from typing import Dict, List, Optional
from database import DatabaseManager
import json

class CookingSkillAdapter:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_skill_level(self, user_id: int) -> str:
        """Get user's cooking skill level"""
        user = self.db.get_user_by_id(user_id)
        if user:
            return user.cooking_skill
        return 'beginner'
    
    def update_skill_level(self, user_id: int, skill_level: str):
        """Update user's cooking skill level"""
        conn = self.db.db_path
        import sqlite3
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET cooking_skill = ? WHERE id = ?
        ''', (skill_level, user_id))
        
        conn.commit()
        conn.close()
    
    def adapt_recipe_for_skill(self, recipe: Dict, skill_level: str) -> Dict:
        """Adapt recipe based on user's cooking skill level"""
        adapted_recipe = recipe.copy()
        
        if skill_level == 'beginner':
            adapted_recipe = self._adapt_for_beginner(adapted_recipe)
        elif skill_level == 'intermediate':
            adapted_recipe = self._adapt_for_intermediate(adapted_recipe)
        elif skill_level == 'advanced':
            adapted_recipe = self._adapt_for_advanced(adapted_recipe)
        
        return adapted_recipe
    
    def _adapt_for_beginner(self, recipe: Dict) -> Dict:
        """Adapt recipe for beginner cooks"""
        adapted = recipe.copy()
        
        # Simplify steps
        steps = adapted.get('steps', [])
        simplified_steps = []
        
        for step in steps:
            # Add more detail and break down complex steps
            simplified_step = self._simplify_step(step)
            simplified_steps.append(simplified_step)
        
        adapted['steps'] = simplified_steps
        
        # Add beginner tips
        adapted['beginner_tips'] = self._get_beginner_tips(recipe)
        
        # Simplify ingredients (remove complex substitutions)
        ingredients = adapted.get('ingredients', [])
        simplified_ingredients = []
        
        for ingredient in ingredients:
            simplified_ingredient = self._simplify_ingredient(ingredient)
            simplified_ingredients.append(simplified_ingredient)
        
        adapted['ingredients'] = simplified_ingredients
        
        # Add prep time estimate
        adapted['prep_time'] = self._estimate_prep_time(recipe, 'beginner')
        
        return adapted
    
    def _adapt_for_intermediate(self, recipe: Dict) -> Dict:
        """Adapt recipe for intermediate cooks"""
        adapted = recipe.copy()
        
        # Add intermediate tips
        adapted['intermediate_tips'] = self._get_intermediate_tips(recipe)
        
        # Add prep time estimate
        adapted['prep_time'] = self._estimate_prep_time(recipe, 'intermediate')
        
        return adapted
    
    def _adapt_for_advanced(self, recipe: Dict) -> Dict:
        """Adapt recipe for advanced cooks"""
        adapted = recipe.copy()
        
        # Add advanced techniques and variations
        adapted['advanced_techniques'] = self._get_advanced_techniques(recipe)
        adapted['variations'] = self._get_recipe_variations(recipe)
        
        # Add prep time estimate
        adapted['prep_time'] = self._estimate_prep_time(recipe, 'advanced')
        
        return adapted
    
    def _simplify_step(self, step: str) -> str:
        """Simplify a cooking step for beginners"""
        # Add more specific instructions
        if 'sauté' in step.lower():
            return f"Heat a pan over medium heat. {step.replace('sauté', 'cook while stirring occasionally')}"
        elif 'simmer' in step.lower():
            return f"Bring to a gentle boil, then reduce heat. {step.replace('simmer', 'let it bubble gently')}"
        elif 'bake' in step.lower():
            return f"Preheat your oven first. {step.replace('bake', 'cook in the oven')}"
        elif 'season' in step.lower():
            return f"Add salt, pepper, and any other spices. {step}"
        else:
            return step
    
    def _simplify_ingredient(self, ingredient: str) -> str:
        """Simplify ingredient description for beginners"""
        # Make measurements more explicit
        if 'tbsp' in ingredient.lower():
            return ingredient.replace('tbsp', 'tablespoon')
        elif 'tsp' in ingredient.lower():
            return ingredient.replace('tsp', 'teaspoon')
        elif 'clove' in ingredient.lower():
            return ingredient.replace('clove', 'piece')
        
        return ingredient
    
    def _get_beginner_tips(self, recipe: Dict) -> List[str]:
        """Get beginner cooking tips for a recipe"""
        tips = []
        
        # General beginner tips
        tips.append("Read through all steps before starting")
        tips.append("Prepare all ingredients before cooking")
        tips.append("Keep a clean workspace")
        
        # Recipe-specific tips
        if any('chicken' in ing.lower() for ing in recipe.get('ingredients', [])):
            tips.append("Chicken is done when juices run clear")
        
        if any('pasta' in ing.lower() for ing in recipe.get('ingredients', [])):
            tips.append("Test pasta by tasting - it should be al dente")
        
        if any('rice' in ing.lower() for ing in recipe.get('ingredients', [])):
            tips.append("Use a 2:1 ratio of water to rice")
        
        return tips
    
    def _get_intermediate_tips(self, recipe: Dict) -> List[str]:
        """Get intermediate cooking tips for a recipe"""
        tips = []
        
        # General intermediate tips
        tips.append("Taste and adjust seasoning as you cook")
        tips.append("Let meat rest before cutting")
        tips.append("Use a meat thermometer for accuracy")
        
        # Recipe-specific tips
        if any('fish' in ing.lower() for ing in recipe.get('ingredients', [])):
            tips.append("Fish is done when it flakes easily with a fork")
        
        if any('vegetables' in ing.lower() for ing in recipe.get('ingredients', [])):
            tips.append("Cut vegetables uniformly for even cooking")
        
        return tips
    
    def _get_advanced_techniques(self, recipe: Dict) -> List[str]:
        """Get advanced cooking techniques for a recipe"""
        techniques = []
        
        # General advanced techniques
        techniques.append("Master the art of seasoning and layering flavors")
        techniques.append("Experiment with different cooking methods")
        techniques.append("Develop your own variations and improvements")
        
        # Recipe-specific techniques
        if any('meat' in ing.lower() for ing in recipe.get('ingredients', [])):
            techniques.append("Try sous vide for perfect doneness")
        
        if any('sauce' in ing.lower() for ing in recipe.get('ingredients', [])):
            techniques.append("Learn to make mother sauces and derivatives")
        
        return techniques
    
    def _get_recipe_variations(self, recipe: Dict) -> List[str]:
        """Get recipe variations for advanced cooks"""
        variations = []
        
        # General variations
        variations.append("Try different protein sources")
        variations.append("Experiment with different cuisines")
        variations.append("Add your own creative twists")
        
        # Recipe-specific variations
        if 'pasta' in recipe.get('name', '').lower():
            variations.append("Try different pasta shapes")
            variations.append("Experiment with different sauces")
        
        if 'salad' in recipe.get('name', '').lower():
            variations.append("Add seasonal ingredients")
            variations.append("Try different dressings")
        
        return variations
    
    def _estimate_prep_time(self, recipe: Dict, skill_level: str) -> str:
        """Estimate prep time based on skill level"""
        base_time = 30  # Base time in minutes
        
        # Adjust based on skill level
        if skill_level == 'beginner':
            base_time += 15  # Beginners take longer
        elif skill_level == 'advanced':
            base_time -= 10  # Advanced cooks are faster
        
        # Adjust based on recipe complexity
        ingredients_count = len(recipe.get('ingredients', []))
        steps_count = len(recipe.get('steps', []))
        
        complexity_factor = (ingredients_count + steps_count) / 10
        estimated_time = int(base_time * (1 + complexity_factor))
        
        return f"{estimated_time} minutes"
    
    def get_skill_recommendations(self, user_id: int) -> List[str]:
        """Get recommendations for improving cooking skills"""
        skill_level = self.get_skill_level(user_id)
        recommendations = []
        
        if skill_level == 'beginner':
            recommendations = [
                "Start with simple one-pot meals",
                "Learn basic knife skills",
                "Practice with eggs (scrambled, fried, boiled)",
                "Master rice and pasta cooking",
                "Learn to season food properly"
            ]
        elif skill_level == 'intermediate':
            recommendations = [
                "Try more complex techniques like braising",
                "Experiment with different cuisines",
                "Learn to make your own stocks and sauces",
                "Practice timing multiple dishes",
                "Develop your palate and taste testing skills"
            ]
        elif skill_level == 'advanced':
            recommendations = [
                "Master advanced techniques like sous vide",
                "Create your own recipes",
                "Learn about food science and chemistry",
                "Experiment with fermentation",
                "Teach others to cook"
            ]
        
        return recommendations

def render_cooking_skills_ui(user_id: int, db_manager: DatabaseManager, lang: str = "en"):
    """Render cooking skills UI"""
    st.title("👨‍🍳 Cooking Skills")
    
    skill_adapter = CookingSkillAdapter(db_manager)
    
    # Get current skill level
    current_skill = skill_adapter.get_skill_level(user_id)
    
    # Display current skill level
    st.subheader("Your Current Skill Level")
    
    skill_colors = {
        'beginner': '🟢',
        'intermediate': '🟡',
        'advanced': '🔴'
    }
    
    st.markdown(f"**{skill_colors.get(current_skill, '🟢')} {current_skill.title()}**")
    
    # Skill level selector
    st.subheader("Update Your Skill Level")
    
    new_skill = st.selectbox(
        "Select your cooking skill level",
        ['beginner', 'intermediate', 'advanced'],
        index=['beginner', 'intermediate', 'advanced'].index(current_skill)
    )
    
    if st.button("Update Skill Level"):
        skill_adapter.update_skill_level(user_id, new_skill)
        st.success("Skill level updated!")
        st.rerun()
    
    # Skill recommendations
    st.subheader("💡 Skill Development Recommendations")
    
    recommendations = skill_adapter.get_skill_recommendations(user_id)
    
    for i, rec in enumerate(recommendations, 1):
        st.write(f"{i}. {rec}")
    
    # Skill level descriptions
    st.subheader("Skill Level Descriptions")
    
    with st.expander("Beginner"):
        st.markdown("""
        **Beginner cooks** are just starting their culinary journey. They:
        - Are learning basic cooking techniques
        - Need detailed, step-by-step instructions
        - Benefit from simplified recipes and clear explanations
        - Are building confidence in the kitchen
        """)
    
    with st.expander("Intermediate"):
        st.markdown("""
        **Intermediate cooks** have some experience and confidence. They:
        - Can follow most recipes without detailed explanations
        - Understand basic cooking principles
        - Can make simple substitutions and modifications
        - Are ready to try more complex techniques
        """)
    
    with st.expander("Advanced"):
        st.markdown("""
        **Advanced cooks** are experienced and confident. They:
        - Can create their own recipes
        - Understand advanced cooking techniques
        - Can make complex substitutions and modifications
        - Are ready to experiment and innovate
        """)
    
    # Skill progress tracking
    st.subheader("Track Your Progress")
    
    # This would track cooking milestones and achievements
    st.info("Skill progress tracking will be implemented in future updates!")
    
    # Cooking tips based on skill level
    st.subheader("Cooking Tips for Your Level")
    
    if current_skill == 'beginner':
        st.markdown("""
        - **Start simple**: Begin with basic recipes and build confidence
        - **Read ahead**: Always read the entire recipe before starting
        - **Prep first**: Get all ingredients ready before cooking
        - **Don't rush**: Take your time and focus on technique
        - **Practice**: The more you cook, the better you'll get
        """)
    elif current_skill == 'intermediate':
        st.markdown("""
        - **Experiment**: Try new ingredients and techniques
        - **Taste as you go**: Adjust seasoning throughout cooking
        - **Learn timing**: Practice cooking multiple dishes simultaneously
        - **Build flavor**: Layer flavors with aromatics and seasonings
        - **Share knowledge**: Teach others what you've learned
        """)
    elif current_skill == 'advanced':
        st.markdown("""
        - **Innovate**: Create your own recipes and techniques
        - **Master fundamentals**: Perfect basic techniques for consistency
        - **Explore cuisines**: Learn about different culinary traditions
        - **Understand science**: Learn the why behind cooking methods
        - **Mentor others**: Share your knowledge and experience
        """)
