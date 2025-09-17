import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from database import DatabaseManager
import json
from datetime import datetime, timedelta
from collections import Counter

class PreferenceLearningSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def learn_from_rating(self, user_id: int, food_item: str, rating: int, meal_type: str = None):
        """Learn from user's food rating"""
        self.db.update_user_preferences(user_id, food_item, rating, meal_type)
        
        # Log analytics event
        self.db.log_analytics_event(
            user_id=user_id,
            event_type='food_rating',
            event_data={
                'food_item': food_item,
                'rating': rating,
                'meal_type': meal_type
            }
        )
    
    def get_user_preferences(self, user_id: int) -> Dict:
        """Get user's learned preferences"""
        return self.db.get_user_preferences(user_id)
    
    def get_recommendations(self, user_id: int, available_recipes: List[Dict], 
                          meal_type: str = None) -> List[Dict]:
        """Get personalized recipe recommendations based on learned preferences"""
        preferences = self.get_user_preferences(user_id)
        
        if not preferences:
            return available_recipes
        
        # Score recipes based on preferences
        scored_recipes = []
        
        for recipe in available_recipes:
            score = self._calculate_preference_score(recipe, preferences, meal_type)
            scored_recipes.append((recipe, score))
        
        # Sort by score (highest first)
        scored_recipes.sort(key=lambda x: x[1], reverse=True)
        
        return [recipe for recipe, score in scored_recipes]
    
    def _calculate_preference_score(self, recipe: Dict, preferences: Dict, 
                                  meal_type: str = None) -> float:
        """Calculate preference score for a recipe"""
        score = 0.0
        total_weight = 0
        
        # Check ingredients
        ingredients = recipe.get('ingredients', [])
        for ingredient in ingredients:
            # Extract main ingredient name (before any measurements)
            ingredient_name = self._extract_ingredient_name(ingredient)
            
            # Check if we have preference data for this ingredient
            for pref_item, pref_data in preferences.items():
                if self._ingredients_match(ingredient_name, pref_item):
                    rating = pref_data['avg_rating']
                    count = pref_data['count']
                    
                    # Weight by confidence (more ratings = higher confidence)
                    weight = min(count / 5.0, 1.0)  # Max weight at 5+ ratings
                    score += rating * weight
                    total_weight += weight
        
        # Check meal type preference
        if meal_type:
            meal_type_prefs = self._get_meal_type_preferences(preferences)
            if meal_type in meal_type_prefs:
                score += meal_type_prefs[meal_type] * 0.5
                total_weight += 0.5
        
        # Check tags preferences
        tags = recipe.get('tags', [])
        tag_prefs = self._get_tag_preferences(preferences)
        for tag in tags:
            if tag in tag_prefs:
                score += tag_prefs[tag] * 0.3
                total_weight += 0.3
        
        return score / max(total_weight, 1.0) if total_weight > 0 else 0.0
    
    def _extract_ingredient_name(self, ingredient: str) -> str:
        """Extract main ingredient name from ingredient string"""
        # Remove measurements and common words
        words = ingredient.lower().split()
        
        # Remove common measurement words
        measurement_words = {'g', 'kg', 'ml', 'l', 'tsp', 'tbsp', 'cup', 'cups', 'oz', 'lb', 'pound', 'pounds'}
        words = [w for w in words if w not in measurement_words]
        
        # Remove numbers
        words = [w for w in words if not w.isdigit()]
        
        # Return the first meaningful word
        return words[0] if words else ingredient.lower()
    
    def _ingredients_match(self, ingredient1: str, ingredient2: str) -> bool:
        """Check if two ingredients are similar"""
        # Simple similarity check
        ingredient1 = ingredient1.lower().strip()
        ingredient2 = ingredient2.lower().strip()
        
        # Exact match
        if ingredient1 == ingredient2:
            return True
        
        # Check if one contains the other
        if ingredient1 in ingredient2 or ingredient2 in ingredient1:
            return True
        
        # Check for common variations
        variations = {
            'chicken': ['poultry', 'breast', 'thigh'],
            'beef': ['meat', 'steak', 'ground'],
            'fish': ['salmon', 'tuna', 'cod', 'seafood'],
            'vegetables': ['veggies', 'veggie', 'vegetable'],
            'cheese': ['dairy', 'mozzarella', 'cheddar', 'feta']
        }
        
        for main, variants in variations.items():
            if (ingredient1 == main and ingredient2 in variants) or \
               (ingredient2 == main and ingredient1 in variants):
                return True
        
        return False
    
    def _get_meal_type_preferences(self, preferences: Dict) -> Dict[str, float]:
        """Extract meal type preferences from user data"""
        meal_types = ['breakfast', 'lunch', 'dinner']
        meal_prefs = {}
        
        for meal_type in meal_types:
            ratings = []
            for pref_item, pref_data in preferences.items():
                # This would need to be stored in the database
                # For now, we'll use a simple heuristic
                if meal_type in pref_item.lower():
                    ratings.append(pref_data['avg_rating'])
            
            if ratings:
                meal_prefs[meal_type] = np.mean(ratings)
        
        return meal_prefs
    
    def _get_tag_preferences(self, preferences: Dict) -> Dict[str, float]:
        """Extract tag preferences from user data"""
        # This would analyze which types of foods (tags) the user prefers
        # For now, return empty dict
        return {}
    
    def get_insights(self, user_id: int) -> Dict:
        """Get insights about user's food preferences"""
        preferences = self.get_user_preferences(user_id)
        
        if not preferences:
            return {
                'total_ratings': 0,
                'favorite_foods': [],
                'disliked_foods': [],
                'preference_confidence': 0
            }
        
        # Analyze preferences
        favorite_foods = []
        disliked_foods = []
        
        for food, data in preferences.items():
            if data['avg_rating'] >= 4.0:
                favorite_foods.append((food, data['avg_rating']))
            elif data['avg_rating'] <= 2.0:
                disliked_foods.append((food, data['avg_rating']))
        
        # Sort by rating
        favorite_foods.sort(key=lambda x: x[1], reverse=True)
        disliked_foods.sort(key=lambda x: x[1])
        
        # Calculate confidence based on number of ratings
        total_ratings = sum(data['count'] for data in preferences.values())
        confidence = min(total_ratings / 20.0, 1.0)  # Max confidence at 20+ ratings
        
        return {
            'total_ratings': total_ratings,
            'favorite_foods': favorite_foods[:5],
            'disliked_foods': disliked_foods[:5],
            'preference_confidence': confidence
        }

def render_preference_learning_ui(user_id: int, db_manager: DatabaseManager, lang: str = "en"):
    """Render preference learning UI"""
    st.title("🍽️ Food Preferences")
    
    learning_system = PreferenceLearningSystem(db_manager)
    
    # Get user insights
    insights = learning_system.get_insights(user_id)
    
    # Display insights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Ratings", insights['total_ratings'])
    
    with col2:
        st.metric("Preference Confidence", f"{insights['preference_confidence']:.1%}")
    
    with col3:
        st.metric("Favorite Foods", len(insights['favorite_foods']))
    
    # Favorite and disliked foods
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("❤️ Favorite Foods")
        if insights['favorite_foods']:
            for food, rating in insights['favorite_foods']:
                st.write(f"• {food} ({rating:.1f}⭐)")
        else:
            st.info("Rate some foods to see your favorites here!")
    
    with col2:
        st.subheader("👎 Disliked Foods")
        if insights['disliked_foods']:
            for food, rating in insights['disliked_foods']:
                st.write(f"• {food} ({rating:.1f}⭐)")
        else:
            st.info("No disliked foods yet")
    
    # Rating interface
    st.subheader("Rate Your Meals")
    
    # Get recent meal plans for rating
    meal_plans = db_manager.get_meal_plans(user_id, limit=5)
    
    if meal_plans:
        st.markdown("Rate the meals from your recent plans:")
        
        for i, plan in enumerate(meal_plans):
            with st.expander(f"Week of {plan['week_start'].strftime('%Y-%m-%d')}"):
                plan_data = plan['plan_data']
                
                for day, meals in plan_data.items():
                    if isinstance(meals, dict):
                        st.write(f"**{day}**")
                        
                        for meal_type, recipe in meals.items():
                            if recipe and isinstance(recipe, dict):
                                col1, col2, col3 = st.columns([2, 1, 1])
                                
                                with col1:
                                    st.write(f"{meal_type.title()}: {recipe.get('name', 'Unknown')}")
                                
                                with col2:
                                    rating = st.selectbox(
                                        "Rating",
                                        [1, 2, 3, 4, 5],
                                        index=4,
                                        key=f"rating_{i}_{day}_{meal_type}"
                                    )
                                
                                with col3:
                                    if st.button("Submit", key=f"submit_{i}_{day}_{meal_type}"):
                                        learning_system.learn_from_rating(
                                            user_id=user_id,
                                            food_item=recipe.get('name', ''),
                                            rating=rating,
                                            meal_type=meal_type
                                        )
                                        st.success("Rating saved!")
                                        st.rerun()
    else:
        st.info("Generate some meal plans first to rate your meals!")
    
    # Manual food rating
    st.subheader("Rate Individual Foods")
    
    with st.form("manual_rating"):
        food_name = st.text_input("Food Name", placeholder="e.g., Grilled Chicken")
        meal_type = st.selectbox("Meal Type", ["breakfast", "lunch", "dinner", "snack"])
        rating = st.selectbox("Rating", [1, 2, 3, 4, 5], index=4)
        
        if st.form_submit_button("Add Rating"):
            learning_system.learn_from_rating(
                user_id=user_id,
                food_item=food_name,
                rating=rating,
                meal_type=meal_type
            )
            st.success("Rating added!")
            st.rerun()
    
    # Preference learning tips
    st.subheader("💡 Tips for Better Recommendations")
    st.markdown("""
    - Rate meals honestly after eating them
    - Rate individual ingredients you particularly like or dislike
    - The more you rate, the better your recommendations become
    - Try new foods and rate them to expand your preferences
    """)
