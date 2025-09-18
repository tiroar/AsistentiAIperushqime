"""
Cloud-compatible utilities for Streamlit Cloud deployment
This module provides alternatives to database operations that work in read-only environments
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class CloudCompatibleStorage:
    """Cloud-compatible storage using Streamlit session state"""
    
    @staticmethod
    def save_meal_plan(user_id: int, plan_data: Dict, timestamp: datetime) -> None:
        """Save meal plan to session state instead of database"""
        if 'meal_plans' not in st.session_state:
            st.session_state.meal_plans = {}
        
        if user_id not in st.session_state.meal_plans:
            st.session_state.meal_plans[user_id] = []
        
        plan_entry = {
            'plan_data': plan_data,
            'timestamp': timestamp.isoformat(),
            'id': len(st.session_state.meal_plans[user_id]) + 1
        }
        
        st.session_state.meal_plans[user_id].append(plan_entry)
        
        # Keep only last 10 plans to avoid memory issues
        if len(st.session_state.meal_plans[user_id]) > 10:
            st.session_state.meal_plans[user_id] = st.session_state.meal_plans[user_id][-10:]
    
    @staticmethod
    def get_meal_plans(user_id: int, limit: int = 5) -> List[Dict]:
        """Get meal plans from session state"""
        if 'meal_plans' not in st.session_state:
            return []
        
        if user_id not in st.session_state.meal_plans:
            return []
        
        return st.session_state.meal_plans[user_id][-limit:]
    
    @staticmethod
    def log_analytics_event(user_id: int, event_type: str, event_data: Dict) -> None:
        """Log analytics event to session state"""
        if 'analytics_events' not in st.session_state:
            st.session_state.analytics_events = {}
        
        if user_id not in st.session_state.analytics_events:
            st.session_state.analytics_events[user_id] = []
        
        event_entry = {
            'event_type': event_type,
            'event_data': event_data,
            'timestamp': datetime.now().isoformat()
        }
        
        st.session_state.analytics_events[user_id].append(event_entry)
        
        # Keep only last 100 events
        if len(st.session_state.analytics_events[user_id]) > 100:
            st.session_state.analytics_events[user_id] = st.session_state.analytics_events[user_id][-100:]
    
    @staticmethod
    def get_analytics_events(user_id: int, limit: int = 50) -> List[Dict]:
        """Get analytics events from session state"""
        if 'analytics_events' not in st.session_state:
            return []
        
        if user_id not in st.session_state.analytics_events:
            return []
        
        return st.session_state.analytics_events[user_id][-limit:]
    
    @staticmethod
    def save_user_preferences(user_id: int, preferences: Dict) -> None:
        """Save user preferences to session state"""
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {}
        
        st.session_state.user_preferences[user_id] = preferences
    
    @staticmethod
    def get_user_preferences(user_id: int) -> Dict:
        """Get user preferences from session state"""
        if 'user_preferences' not in st.session_state:
            return {}
        
        return st.session_state.user_preferences.get(user_id, {})
    
    @staticmethod
    def save_cooking_skills(user_id: int, skills: Dict) -> None:
        """Save cooking skills to session state"""
        if 'cooking_skills' not in st.session_state:
            st.session_state.cooking_skills = {}
        
        st.session_state.cooking_skills[user_id] = skills
    
    @staticmethod
    def get_cooking_skills(user_id: int) -> Dict:
        """Get cooking skills from session state"""
        if 'cooking_skills' not in st.session_state:
            return {}
        
        return st.session_state.cooking_skills.get(user_id, {})
    
    @staticmethod
    def save_achievements(user_id: int, achievements: List[str]) -> None:
        """Save achievements to session state"""
        if 'achievements' not in st.session_state:
            st.session_state.achievements = {}
        
        st.session_state.achievements[user_id] = achievements
    
    @staticmethod
    def get_achievements(user_id: int) -> List[str]:
        """Get achievements from session state"""
        if 'achievements' not in st.session_state:
            return []
        
        return st.session_state.achievements.get(user_id, [])

class CloudCompatibleDatabaseManager:
    """Cloud-compatible database manager that uses session state"""
    
    def __init__(self, db_path: str = "meal_planner.db"):
        self.db_path = db_path
        self.storage = CloudCompatibleStorage()
    
    def save_meal_plan(self, user_id: int, plan_data: Dict, timestamp: datetime) -> None:
        """Save meal plan using cloud-compatible storage"""
        self.storage.save_meal_plan(user_id, plan_data, timestamp)
    
    def get_meal_plans(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get meal plans using cloud-compatible storage"""
        return self.storage.get_meal_plans(user_id, limit)
    
    def log_analytics_event(self, user_id: int, event_type: str, event_data: Dict) -> None:
        """Log analytics event using cloud-compatible storage"""
        self.storage.log_analytics_event(user_id, event_type, event_data)
    
    def get_analytics_events(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get analytics events using cloud-compatible storage"""
        return self.storage.get_analytics_events(user_id, limit)
    
    def save_user_preferences(self, user_id: int, preferences: Dict) -> None:
        """Save user preferences using cloud-compatible storage"""
        self.storage.save_user_preferences(user_id, preferences)
    
    def get_user_preferences(self, user_id: int) -> Dict:
        """Get user preferences using cloud-compatible storage"""
        return self.storage.get_user_preferences(user_id)
    
    def save_cooking_skills(self, user_id: int, skills: Dict) -> None:
        """Save cooking skills using cloud-compatible storage"""
        self.storage.save_cooking_skills(user_id, skills)
    
    def get_cooking_skills(self, user_id: int) -> Dict:
        """Get cooking skills using cloud-compatible storage"""
        return self.storage.get_cooking_skills(user_id)
    
    def save_achievements(self, user_id: int, achievements: List[str]) -> None:
        """Save achievements using cloud-compatible storage"""
        self.storage.save_achievements(user_id, achievements)
    
    def get_achievements(self, user_id: int) -> List[str]:
        """Get achievements using cloud-compatible storage"""
        return self.storage.get_achievements(user_id)
    
    def get_user_by_id(self, user_id: int) -> Optional[Any]:
        """Get user by ID - returns a mock user for cloud compatibility"""
        from database import User
        from datetime import datetime
        
        # For cloud deployment, we'll create a proper User object
        return User(
            id=user_id,
            email=f"user{user_id}@example.com",
            username=f"user{user_id}",
            auth_provider="cloud",
            created_at=datetime.now(),
            last_login=datetime.now(),
            profile_data=self.storage.get_user_preferences(user_id),
            preferences=self.storage.get_user_preferences(user_id),
            cooking_skill=self.storage.get_cooking_skills(user_id).get('level', 'beginner'),
            achievements=self.storage.get_achievements(user_id),
            friends=[],
            is_active=True
        )
    
    def get_user_by_email(self, email: str) -> Optional[Any]:
        """Get user by email - returns None for cloud compatibility"""
        # For cloud deployment, we can't look up users by email
        # This is handled by the AuthManager for guest users
        return None
