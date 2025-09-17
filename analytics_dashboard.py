import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List
from database import DatabaseManager
import json

class AnalyticsDashboard:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_user_analytics(self, user_id: int, days: int = 30) -> Dict:
        """Get comprehensive user analytics"""
        # Get analytics events
        events = self.db.get_analytics_data(user_id, days)
        
        # Get meal plans
        meal_plans = self.db.get_meal_plans(user_id, limit=50)
        
        # Get nutrition reports
        nutrition_reports = self.db.get_nutrition_reports(user_id, limit=12)
        
        # Get user preferences
        preferences = self.db.get_user_preferences(user_id)
        
        # Calculate insights
        insights = self._calculate_insights(events, meal_plans, nutrition_reports, preferences)
        
        return {
            'events': events,
            'meal_plans': meal_plans,
            'nutrition_reports': nutrition_reports,
            'preferences': preferences,
            'insights': insights
        }
    
    def _calculate_insights(self, events: Dict, meal_plans: List, 
                          nutrition_reports: List, preferences: Dict) -> Dict:
        """Calculate insights from user data"""
        insights = {}
        
        # Activity insights
        insights['total_meal_plans'] = len(meal_plans)
        insights['total_nutrition_reports'] = len(nutrition_reports)
        insights['total_food_ratings'] = sum(data['count'] for data in preferences.values())
        
        # Consistency insights
        if meal_plans:
            plan_dates = [plan['week_start'] for plan in meal_plans]
            plan_dates.sort()
            
            # Calculate streak
            current_streak = 0
            if plan_dates:
                last_date = plan_dates[-1]
                current_date = datetime.now()
                
                # Check if last plan was within 7 days
                if (current_date - last_date).days <= 7:
                    current_streak = 1
                    
                    # Count consecutive weeks
                    for i in range(len(plan_dates) - 2, -1, -1):
                        if (plan_dates[i + 1] - plan_dates[i]).days <= 7:
                            current_streak += 1
                        else:
                            break
            
            insights['current_streak'] = current_streak
            insights['longest_streak'] = self._calculate_longest_streak(plan_dates)
        
        # Nutrition insights
        if nutrition_reports:
            recent_reports = nutrition_reports[:4]  # Last 4 weeks
            
            # Calculate averages
            avg_calories = sum(r.avg_daily_calories for r in recent_reports) / len(recent_reports)
            avg_protein = sum(r.protein_avg for r in recent_reports) / len(recent_reports)
            avg_carbs = sum(r.carbs_avg for r in recent_reports) / len(recent_reports)
            avg_fat = sum(r.fat_avg for r in recent_reports) / len(recent_reports)
            
            insights['avg_daily_calories'] = round(avg_calories, 0)
            insights['avg_protein'] = round(avg_protein, 1)
            insights['avg_carbs'] = round(avg_carbs, 1)
            insights['avg_fat'] = round(avg_fat, 1)
            
            # Goal achievement rate
            goal_achievements = []
            for report in recent_reports:
                goals_met = report.goals_met
                if goals_met:
                    met_count = sum(1 for goal in goals_met.values() if goal.get('met', False))
                    total_count = len(goals_met)
                    if total_count > 0:
                        goal_achievements.append(met_count / total_count)
            
            insights['goal_achievement_rate'] = round(
                sum(goal_achievements) / len(goal_achievements) * 100, 1
            ) if goal_achievements else 0
        
        # Preference insights
        if preferences:
            # Most liked foods
            liked_foods = [
                (food, data['avg_rating']) for food, data in preferences.items()
                if data['avg_rating'] >= 4.0
            ]
            liked_foods.sort(key=lambda x: x[1], reverse=True)
            insights['favorite_foods'] = liked_foods[:5]
            
            # Most rated foods
            rated_foods = [
                (food, data['count']) for food, data in preferences.items()
            ]
            rated_foods.sort(key=lambda x: x[1], reverse=True)
            insights['most_rated_foods'] = rated_foods[:5]
        
        return insights
    
    def _calculate_longest_streak(self, plan_dates: List[datetime]) -> int:
        """Calculate longest streak of meal planning"""
        if not plan_dates:
            return 0
        
        plan_dates.sort()
        longest_streak = 1
        current_streak = 1
        
        for i in range(1, len(plan_dates)):
            if (plan_dates[i] - plan_dates[i-1]).days <= 7:
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            else:
                current_streak = 1
        
        return longest_streak

def render_analytics_dashboard(user_id: int, db_manager: DatabaseManager, lang: str = "en"):
    """Render comprehensive analytics dashboard"""
    st.title("📊 Analytics Dashboard")
    
    analytics = AnalyticsDashboard(db_manager)
    
    # Get analytics data
    with st.spinner("Loading analytics..."):
        data = analytics.get_user_analytics(user_id)
    
    insights = data['insights']
    
    # Key metrics
    st.subheader("📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Meal Plans",
            insights.get('total_meal_plans', 0),
            delta=f"{insights.get('current_streak', 0)} week streak"
        )
    
    with col2:
        st.metric(
            "Food Ratings",
            insights.get('total_food_ratings', 0),
            delta="preferences learned"
        )
    
    with col3:
        st.metric(
            "Goal Achievement",
            f"{insights.get('goal_achievement_rate', 0):.1f}%",
            delta="last 4 weeks"
        )
    
    with col4:
        st.metric(
            "Longest Streak",
            f"{insights.get('longest_streak', 0)} weeks",
            delta="meal planning"
        )
    
    # Activity overview
    st.subheader("📅 Activity Overview")
    
    # Event timeline
    events = data['events']
    if events:
        event_df = pd.DataFrame([
            {'Event Type': event, 'Count': count}
            for event, count in events.items()
        ])
        
        fig = px.bar(event_df, x='Event Type', y='Count', 
                    title="Activity by Event Type")
        st.plotly_chart(fig, use_container_width=True)
    
    # Meal planning trends
    st.subheader("🍽️ Meal Planning Trends")
    
    meal_plans = data['meal_plans']
    if meal_plans:
        # Create timeline data
        timeline_data = []
        for plan in meal_plans:
            timeline_data.append({
                'Date': plan['week_start'],
                'Week': plan['week_start'].strftime('%Y-%m-%d'),
                'Plans': 1
            })
        
        timeline_df = pd.DataFrame(timeline_data)
        timeline_df = timeline_df.groupby('Week').sum().reset_index()
        
        fig = px.line(timeline_df, x='Week', y='Plans', 
                     title="Meal Plans Over Time")
        st.plotly_chart(fig, use_container_width=True)
    
    # Nutrition trends
    st.subheader("🥗 Nutrition Trends")
    
    nutrition_reports = data['nutrition_reports']
    if nutrition_reports:
        # Prepare nutrition data
        nutrition_data = []
        for report in nutrition_reports:
            nutrition_data.append({
                'Week': report.week_start.strftime('%Y-%m-%d'),
                'Calories': report.avg_daily_calories,
                'Protein': report.protein_avg,
                'Carbs': report.carbs_avg,
                'Fat': report.fat_avg
            })
        
        nutrition_df = pd.DataFrame(nutrition_data)
        
        # Create nutrition chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=nutrition_df['Week'],
            y=nutrition_df['Calories'],
            mode='lines+markers',
            name='Calories',
            line=dict(color='#FF6B6B')
        ))
        
        fig.add_trace(go.Scatter(
            x=nutrition_df['Week'],
            y=nutrition_df['Protein'],
            mode='lines+markers',
            name='Protein (g)',
            line=dict(color='#4ECDC4'),
            yaxis='y2'
        ))
        
        fig.add_trace(go.Scatter(
            x=nutrition_df['Week'],
            y=nutrition_df['Carbs'],
            mode='lines+markers',
            name='Carbs (g)',
            line=dict(color='#45B7D1'),
            yaxis='y2'
        ))
        
        fig.add_trace(go.Scatter(
            x=nutrition_df['Week'],
            y=nutrition_df['Fat'],
            mode='lines+markers',
            name='Fat (g)',
            line=dict(color='#96CEB4'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Nutrition Trends Over Time",
            xaxis_title="Week",
            yaxis=dict(title="Calories", side="left"),
            yaxis2=dict(title="Macros (g)", side="right", overlaying="y"),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Food preferences
    st.subheader("🍽️ Food Preferences")
    
    preferences = data['preferences']
    if preferences:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Favorite Foods**")
            favorite_foods = insights.get('favorite_foods', [])
            if favorite_foods:
                for food, rating in favorite_foods:
                    st.write(f"• {food} ({rating:.1f}⭐)")
            else:
                st.info("No favorite foods yet")
        
        with col2:
            st.markdown("**Most Rated Foods**")
            most_rated = insights.get('most_rated_foods', [])
            if most_rated:
                for food, count in most_rated:
                    st.write(f"• {food} ({count} ratings)")
            else:
                st.info("No rated foods yet")
    
    # Detailed analytics
    st.subheader("📋 Detailed Analytics")
    
    with st.expander("View Raw Data"):
        # Events data
        if events:
            st.markdown("**Events Data**")
            events_df = pd.DataFrame([
                {'Event Type': event, 'Count': count}
                for event, count in events.items()
            ])
            st.dataframe(events_df, use_container_width=True)
        
        # Meal plans data
        if meal_plans:
            st.markdown("**Meal Plans Data**")
            plans_df = pd.DataFrame([
                {
                    'Week Start': plan['week_start'].strftime('%Y-%m-%d'),
                    'Created At': plan['created_at'].strftime('%Y-%m-%d %H:%M'),
                    'Plan ID': plan.get('id', 'N/A')
                }
                for plan in meal_plans
            ])
            st.dataframe(plans_df, use_container_width=True)
        
        # Nutrition reports data
        if nutrition_reports:
            st.markdown("**Nutrition Reports Data**")
            reports_df = pd.DataFrame([
                {
                    'Week Start': report.week_start.strftime('%Y-%m-%d'),
                    'Avg Calories': report.avg_daily_calories,
                    'Avg Protein': report.protein_avg,
                    'Avg Carbs': report.carbs_avg,
                    'Avg Fat': report.fat_avg,
                    'Weight Change': report.weight_change
                }
                for report in nutrition_reports
            ])
            st.dataframe(reports_df, use_container_width=True)
    
    # Export data
    st.subheader("📤 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export Events Data"):
            if events:
                events_df = pd.DataFrame([
                    {'Event Type': event, 'Count': count}
                    for event, count in events.items()
                ])
                csv = events_df.to_csv(index=False)
                st.download_button(
                    "Download Events CSV",
                    data=csv,
                    file_name=f"events_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    with col2:
        if st.button("Export Nutrition Data"):
            if nutrition_reports:
                reports_df = pd.DataFrame([
                    {
                        'Week Start': report.week_start.strftime('%Y-%m-%d'),
                        'Avg Calories': report.avg_daily_calories,
                        'Avg Protein': report.protein_avg,
                        'Avg Carbs': report.carbs_avg,
                        'Avg Fat': report.fat_avg,
                        'Weight Change': report.weight_change
                    }
                    for report in nutrition_reports
                ])
                csv = reports_df.to_csv(index=False)
                st.download_button(
                    "Download Nutrition CSV",
                    data=csv,
                    file_name=f"nutrition_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    with col3:
        if st.button("Export All Data"):
            # Create comprehensive export
            export_data = {
                'user_id': user_id,
                'export_date': datetime.now().isoformat(),
                'insights': insights,
                'events': events,
                'meal_plans_count': len(meal_plans),
                'nutrition_reports_count': len(nutrition_reports),
                'preferences_count': len(preferences)
            }
            
            json_data = json.dumps(export_data, indent=2, default=str)
            st.download_button(
                "Download All Data (JSON)",
                data=json_data,
                file_name=f"analytics_export_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
