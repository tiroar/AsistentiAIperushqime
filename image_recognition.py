import streamlit as st
import requests
import json
import base64
from typing import Dict, List, Optional, Tuple
from database import DatabaseManager
import os
from datetime import datetime
import io
from PIL import Image

class FoodImageRecognition:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.api_key = os.getenv("OPENAI_API_KEY", "")
    
    def recognize_food(self, image_data: bytes, user_id: int) -> Dict:
        """Recognize food in uploaded image"""
        try:
            # Use OpenAI Vision API for food recognition
            if self.api_key:
                return self._recognize_with_openai(image_data, user_id)
            else:
                return self._recognize_with_fallback(image_data, user_id)
        except Exception as e:
            st.error(f"Food recognition failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'recognized_foods': [],
                'confidence_scores': []
            }
    
    def _recognize_with_openai(self, image_data: bytes, user_id: int) -> Dict:
        """Recognize food using OpenAI Vision API"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this food image and identify:
                                1. All visible food items
                                2. Estimated portion sizes
                                3. Cooking method (raw, cooked, fried, etc.)
                                4. Confidence level for each item (0-100%)
                                
                                Return as JSON with this structure:
                                {
                                    "foods": [
                                        {
                                            "name": "food item name",
                                            "portion": "estimated portion",
                                            "cooking_method": "raw/cooked/fried/etc",
                                            "confidence": 85
                                        }
                                    ]
                                }"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
                
                foods = result.get('foods', [])
                recognized_foods = [food['name'] for food in foods]
                confidence_scores = [food['confidence'] for food in foods]
                
                # Log recognition
                self._log_recognition(user_id, recognized_foods, confidence_scores)
                
                return {
                    'success': True,
                    'recognized_foods': recognized_foods,
                    'confidence_scores': confidence_scores,
                    'detailed_results': foods
                }
            else:
                return self._recognize_with_fallback(image_data, user_id)
                
        except Exception as e:
            st.error(f"OpenAI recognition failed: {str(e)}")
            return self._recognize_with_fallback(image_data, user_id)
    
    def _recognize_with_fallback(self, image_data: bytes, user_id: int) -> Dict:
        """Fallback food recognition using simple heuristics"""
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Simple color-based food detection
            colors = image.getcolors(maxcolors=256*256*256)
            if not colors:
                return {
                    'success': False,
                    'error': 'Could not analyze image',
                    'recognized_foods': [],
                    'confidence_scores': []
                }
            
            # Get dominant colors
            dominant_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:5]
            
            # Simple food detection based on colors
            recognized_foods = []
            confidence_scores = []
            
            for count, color in dominant_colors:
                r, g, b = color
                
                # Green foods (vegetables)
                if g > r and g > b and g > 100:
                    recognized_foods.append("Green vegetables")
                    confidence_scores.append(60)
                
                # Red foods (tomatoes, meat)
                elif r > g and r > b and r > 100:
                    recognized_foods.append("Red food (meat/tomatoes)")
                    confidence_scores.append(50)
                
                # Brown foods (bread, meat)
                elif r > 80 and g > 80 and b < 100:
                    recognized_foods.append("Brown food (bread/meat)")
                    confidence_scores.append(45)
                
                # White foods (rice, pasta)
                elif r > 150 and g > 150 and b > 150:
                    recognized_foods.append("White food (rice/pasta)")
                    confidence_scores.append(40)
            
            # Remove duplicates and limit results
            unique_foods = []
            unique_confidences = []
            seen = set()
            
            for food, conf in zip(recognized_foods, confidence_scores):
                if food not in seen:
                    unique_foods.append(food)
                    unique_confidences.append(conf)
                    seen.add(food)
            
            # Log recognition
            self._log_recognition(user_id, unique_foods, unique_confidences)
            
            return {
                'success': True,
                'recognized_foods': unique_foods[:3],  # Limit to 3 items
                'confidence_scores': unique_confidences[:3],
                'detailed_results': [
                    {
                        'name': food,
                        'portion': 'Unknown',
                        'cooking_method': 'Unknown',
                        'confidence': conf
                    }
                    for food, conf in zip(unique_foods[:3], unique_confidences[:3])
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'recognized_foods': [],
                'confidence_scores': []
            }
    
    def _log_recognition(self, user_id: int, recognized_foods: List[str], 
                        confidence_scores: List[int]):
        """Log food recognition results"""
        try:
            conn = self.db.db_path
            import sqlite3
            conn = sqlite3.connect(conn)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO food_recognition_logs 
                (user_id, recognized_foods, confidence_scores, created_at)
                VALUES (?, ?, ?, ?)
            ''', (
                user_id,
                json.dumps(recognized_foods),
                json.dumps(confidence_scores),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            # Log analytics event
            self.db.log_analytics_event(
                user_id=user_id,
                event_type='food_recognition',
                event_data={
                    'recognized_foods': recognized_foods,
                    'confidence_scores': confidence_scores
                }
            )
            
        except Exception as e:
            st.error(f"Failed to log recognition: {str(e)}")
    
    def get_recognition_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's food recognition history"""
        try:
            conn = self.db.db_path
            import sqlite3
            conn = sqlite3.connect(conn)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT recognized_foods, confidence_scores, created_at
                FROM food_recognition_logs 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'recognized_foods': json.loads(row[0] or '[]'),
                    'confidence_scores': json.loads(row[1] or '[]'),
                    'created_at': datetime.fromisoformat(row[2])
                })
            
            conn.close()
            return history
            
        except Exception as e:
            st.error(f"Failed to get recognition history: {str(e)}")
            return []
    
    def estimate_nutrition(self, recognized_foods: List[str], 
                          confidence_scores: List[int]) -> Dict:
        """Estimate nutrition for recognized foods"""
        # Simple nutrition estimation based on common foods
        nutrition_db = {
            'chicken': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6},
            'beef': {'calories': 250, 'protein': 26, 'carbs': 0, 'fat': 15},
            'fish': {'calories': 206, 'protein': 22, 'carbs': 0, 'fat': 12},
            'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3},
            'pasta': {'calories': 131, 'protein': 5, 'carbs': 25, 'fat': 1.1},
            'bread': {'calories': 265, 'protein': 9, 'carbs': 49, 'fat': 3.2},
            'vegetables': {'calories': 25, 'protein': 2, 'carbs': 5, 'fat': 0.2},
            'fruits': {'calories': 60, 'protein': 0.5, 'carbs': 15, 'fat': 0.2},
            'cheese': {'calories': 113, 'protein': 7, 'carbs': 1, 'fat': 9},
            'eggs': {'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11}
        }
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        for food, confidence in zip(recognized_foods, confidence_scores):
            food_lower = food.lower()
            
            # Find matching nutrition data
            for db_food, nutrition in nutrition_db.items():
                if db_food in food_lower:
                    # Adjust by confidence
                    factor = confidence / 100.0
                    
                    total_calories += nutrition['calories'] * factor
                    total_protein += nutrition['protein'] * factor
                    total_carbs += nutrition['carbs'] * factor
                    total_fat += nutrition['fat'] * factor
                    break
        
        return {
            'calories': round(total_calories),
            'protein': round(total_protein, 1),
            'carbs': round(total_carbs, 1),
            'fat': round(total_fat, 1)
        }

def render_image_recognition_ui(user_id: int, db_manager: DatabaseManager, lang: str = "en"):
    """Render image recognition UI"""
    st.title("📸 Food Recognition")
    
    recognition = FoodImageRecognition(db_manager)
    
    # Upload image
    st.subheader("Upload Food Image")
    
    uploaded_file = st.file_uploader(
        "Choose an image of food",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a clear image of food to get nutrition information"
    )
    
    if uploaded_file is not None:
        # Display image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        # Recognize food
        if st.button("Recognize Food"):
            with st.spinner("Analyzing image..."):
                image_data = uploaded_file.read()
                result = recognition.recognize_food(image_data, user_id)
            
            if result['success']:
                st.success("Food recognition completed!")
                
                # Display results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Recognized Foods")
                    for i, (food, confidence) in enumerate(zip(
                        result['recognized_foods'], 
                        result['confidence_scores']
                    )):
                        st.write(f"• {food} ({confidence}% confidence)")
                
                with col2:
                    st.subheader("Estimated Nutrition")
                    nutrition = recognition.estimate_nutrition(
                        result['recognized_foods'],
                        result['confidence_scores']
                    )
                    
                    st.metric("Calories", nutrition['calories'])
                    st.metric("Protein", f"{nutrition['protein']}g")
                    st.metric("Carbs", f"{nutrition['carbs']}g")
                    st.metric("Fat", f"{nutrition['fat']}g")
                
                # Detailed results
                if 'detailed_results' in result:
                    st.subheader("Detailed Analysis")
                    for food_data in result['detailed_results']:
                        with st.expander(f"{food_data['name']} - {food_data['confidence']}% confidence"):
                            st.write(f"**Portion:** {food_data['portion']}")
                            st.write(f"**Cooking Method:** {food_data['cooking_method']}")
                            st.write(f"**Confidence:** {food_data['confidence']}%")
                
                # Add to meal plan option
                st.subheader("Add to Meal Plan")
                
                meal_type = st.selectbox(
                    "Meal Type",
                    ["breakfast", "lunch", "dinner", "snack"]
                )
                
                if st.button("Add to Today's Plan"):
                    st.info("This would add the recognized food to your meal plan")
                    # Implementation would go here
            else:
                st.error(f"Recognition failed: {result.get('error', 'Unknown error')}")
    
    # Recognition history
    st.subheader("Recognition History")
    
    history = recognition.get_recognition_history(user_id, limit=10)
    
    if history:
        for i, entry in enumerate(history):
            with st.expander(f"Recognition {i+1} - {entry['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Recognized Foods:**")
                    for food in entry['recognized_foods']:
                        st.write(f"• {food}")
                
                with col2:
                    st.write("**Confidence Scores:**")
                    for conf in entry['confidence_scores']:
                        st.write(f"• {conf}%")
    else:
        st.info("No recognition history yet")
    
    # Tips for better recognition
    st.subheader("💡 Tips for Better Recognition")
    st.markdown("""
    - Take clear, well-lit photos
    - Ensure food items are clearly visible
    - Avoid blurry or dark images
    - Try to capture the entire meal
    - Good lighting improves accuracy
    """)
    
    # API key status
    if recognition.api_key:
        st.success("✅ OpenAI API key configured - using advanced recognition")
    else:
        st.warning("⚠️ No API key - using basic recognition. Set OPENAI_API_KEY for better results")
