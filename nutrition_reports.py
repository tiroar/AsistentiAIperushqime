import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any
from database import DatabaseManager, NutritionReport
import json

class NutritionReportGenerator:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def generate_weekly_report(self, user_id: int, week_start: datetime, 
                             meal_plans: List[Dict], progress_data: Dict = None) -> NutritionReport:
        """Generate comprehensive weekly nutrition report"""
        
        # Calculate nutrition totals for the week
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        days_with_meals = 0
        
        for plan in meal_plans:
            if plan.get('plan_data'):
                plan_data = plan['plan_data']
                for day, meals in plan_data.items():
                    if isinstance(meals, dict):
                        day_calories = 0
                        day_protein = 0
                        day_carbs = 0
                        day_fat = 0
                        
                        for meal_type, recipe in meals.items():
                            if recipe and isinstance(recipe, dict):
                                day_calories += recipe.get('kcal', 0)
                                day_protein += recipe.get('protein', 0)
                                day_carbs += recipe.get('carbs', 0)
                                day_fat += recipe.get('fat', 0)
                        
                        if day_calories > 0:
                            total_calories += day_calories
                            total_protein += day_protein
                            total_carbs += day_carbs
                            total_fat += day_fat
                            days_with_meals += 1
        
        # Calculate averages
        avg_daily_calories = total_calories / max(days_with_meals, 1)
        protein_avg = total_protein / max(days_with_meals, 1)
        carbs_avg = total_carbs / max(days_with_meals, 1)
        fat_avg = total_fat / max(days_with_meals, 1)
        
        # Get user's goals
        user = self.db.get_user_by_id(user_id)
        if not user:
            return None
        
        # Calculate goals met
        goals_met = self._calculate_goals_met(user, avg_daily_calories, protein_avg, carbs_avg, fat_avg)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            user, avg_daily_calories, protein_avg, carbs_avg, fat_avg, goals_met
        )
        
        # Calculate weight change
        weight_change = 0
        if progress_data:
            weight_change = progress_data.get('weight_change', 0)
        
        # Create nutrition report
        nutrition_data = {
            'total_calories': total_calories,
            'avg_daily_calories': int(avg_daily_calories),
            'protein_avg': round(protein_avg, 1),
            'carbs_avg': round(carbs_avg, 1),
            'fat_avg': round(fat_avg, 1),
            'weight_change': weight_change,
            'goals_met': goals_met
        }
        
        report = self.db.create_nutrition_report(
            user_id=user_id,
            week_start=week_start,
            nutrition_data=nutrition_data,
            recommendations=recommendations
        )
        
        return report
    
    def _calculate_goals_met(self, user, avg_calories: float, protein: float, 
                           carbs: float, fat: float) -> Dict:
        """Calculate which nutrition goals were met"""
        goals_met = {}
        
        # Get user's target calories and macros
        profile = user.profile_data
        if not profile:
            return goals_met
        
        # Calculate TDEE and targets (simplified)
        age = profile.get('age', 28)
        height = profile.get('height', 178)
        weight = profile.get('weight', 78)
        gender = profile.get('gender', 'Male')
        
        # Basic TDEE calculation
        bmr = 10 * weight + 6.25 * height - 5 * age + (5 if gender == 'Male' else -161)
        tdee = bmr * 1.55  # Moderate activity
        target_calories = int(tdee * 0.85)  # Weight loss
        
        # Protein target (1.7g per kg for weight loss)
        target_protein = weight * 1.7
        
        # Macro targets (30/40/30 for weight loss)
        target_carbs = (target_calories * 0.4) / 4
        target_fat = (target_calories * 0.3) / 9
        
        # Check goals
        goals_met['calories'] = {
            'target': target_calories,
            'actual': int(avg_calories),
            'met': abs(avg_calories - target_calories) <= target_calories * 0.1,
            'percentage': round((avg_calories / target_calories) * 100, 1)
        }
        
        goals_met['protein'] = {
            'target': round(target_protein, 1),
            'actual': round(protein, 1),
            'met': protein >= target_protein * 0.9,
            'percentage': round((protein / target_protein) * 100, 1)
        }
        
        goals_met['carbs'] = {
            'target': round(target_carbs, 1),
            'actual': round(carbs, 1),
            'met': abs(carbs - target_carbs) <= target_carbs * 0.2,
            'percentage': round((carbs / target_carbs) * 100, 1)
        }
        
        goals_met['fat'] = {
            'target': round(target_fat, 1),
            'actual': round(fat, 1),
            'met': abs(fat - target_fat) <= target_fat * 0.2,
            'percentage': round((fat / target_fat) * 100, 1)
        }
        
        return goals_met
    
    def _generate_recommendations(self, user, avg_calories: float, protein: float, 
                                carbs: float, fat: float, goals_met: Dict) -> List[str]:
        """Generate personalized nutrition recommendations"""
        recommendations = []
        
        # Calorie recommendations
        if not goals_met.get('calories', {}).get('met', False):
            cal_percentage = goals_met.get('calories', {}).get('percentage', 100)
            if cal_percentage > 110:
                recommendations.append("Consider reducing portion sizes to meet your calorie target")
            elif cal_percentage < 90:
                recommendations.append("Add healthy snacks to increase your daily calorie intake")
        
        # Protein recommendations
        if not goals_met.get('protein', {}).get('met', False):
            recommendations.append("Increase protein intake with lean meats, fish, or plant-based sources")
        
        # Carb recommendations
        if not goals_met.get('carbs', {}).get('met', False):
            recommendations.append("Focus on complex carbohydrates like whole grains and vegetables")
        
        # Fat recommendations
        if not goals_met.get('fat', {}).get('met', False):
            recommendations.append("Include healthy fats like olive oil, nuts, and avocado")
        
        # General recommendations
        if len([g for g in goals_met.values() if g.get('met', False)]) >= 3:
            recommendations.append("Great job! You're meeting most of your nutrition goals")
        
        if not recommendations:
            recommendations.append("Keep up the excellent work! Your nutrition is well-balanced")
        
        return recommendations

def render_nutrition_dashboard(user_id: int, db_manager: DatabaseManager, lang: str = "en"):
    """Render comprehensive nutrition dashboard"""
    st.title("📊 Nutrition Dashboard")
    
    # Get user's recent reports
    reports = db_manager.get_nutrition_reports(user_id, limit=12)
    
    if not reports:
        st.info("No nutrition reports available yet. Generate some meal plans to see your progress!")
        return
    
    # Latest report
    latest_report = reports[0]
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Avg Daily Calories",
            f"{latest_report.avg_daily_calories:,}",
            delta=f"{latest_report.weight_change:.1f} kg"
        )
    
    with col2:
        st.metric(
            "Protein (g)",
            f"{latest_report.protein_avg:.1f}",
            delta="g/day"
        )
    
    with col3:
        st.metric(
            "Carbs (g)",
            f"{latest_report.carbs_avg:.1f}",
            delta="g/day"
        )
    
    with col4:
        st.metric(
            "Fat (g)",
            f"{latest_report.fat_avg:.1f}",
            delta="g/day"
        )
    
    # Goals progress
    st.subheader("🎯 Goals Progress")
    
    goals = latest_report.goals_met
    
    for nutrient, data in goals.items():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            progress = min(data['percentage'] / 100, 1.0)
            st.progress(progress)
            st.caption(f"{nutrient.title()}: {data['actual']} / {data['target']} {nutrient}")
        
        with col2:
            if data['met']:
                st.success("✅")
            else:
                st.warning("⚠️")
    
    # Recommendations
    st.subheader("💡 Recommendations")
    for rec in latest_report.recommendations:
        st.info(f"• {rec}")
    
    # Historical trends
    if len(reports) > 1:
        st.subheader("📈 Trends Over Time")
        
        # Prepare data for plotting
        df_data = []
        for report in reversed(reports):
            df_data.append({
                'Week': report.week_start.strftime('%Y-%m-%d'),
                'Calories': report.avg_daily_calories,
                'Protein': report.protein_avg,
                'Carbs': report.carbs_avg,
                'Fat': report.fat_avg
            })
        
        df = pd.DataFrame(df_data)
        
        # Create line chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['Week'],
            y=df['Calories'],
            mode='lines+markers',
            name='Calories',
            line=dict(color='#FF6B6B')
        ))
        
        fig.add_trace(go.Scatter(
            x=df['Week'],
            y=df['Protein'],
            mode='lines+markers',
            name='Protein (g)',
            line=dict(color='#4ECDC4'),
            yaxis='y2'
        ))
        
        fig.add_trace(go.Scatter(
            x=df['Week'],
            y=df['Carbs'],
            mode='lines+markers',
            name='Carbs (g)',
            line=dict(color='#45B7D1'),
            yaxis='y2'
        ))
        
        fig.add_trace(go.Scatter(
            x=df['Week'],
            y=df['Fat'],
            mode='lines+markers',
            name='Fat (g)',
            line=dict(color='#96CEB4'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Nutrition Trends",
            xaxis_title="Week",
            yaxis=dict(title="Calories", side="left"),
            yaxis2=dict(title="Macros (g)", side="right", overlaying="y"),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed breakdown
    st.subheader("📋 Detailed Breakdown")
    
    with st.expander("View All Reports"):
        report_data = []
        for report in reports:
            report_data.append({
                'Week': report.week_start.strftime('%Y-%m-%d'),
                'Calories': report.avg_daily_calories,
                'Protein': f"{report.protein_avg:.1f}g",
                'Carbs': f"{report.carbs_avg:.1f}g",
                'Fat': f"{report.fat_avg:.1f}g",
                'Weight Change': f"{report.weight_change:.1f}kg"
            })
        
        report_df = pd.DataFrame(report_data)
        st.dataframe(report_df, use_container_width=True)
        
        # Download button
        csv = report_df.to_csv(index=False)
        st.download_button(
            "Download Nutrition Report (CSV)",
            data=csv,
            file_name=f"nutrition_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
