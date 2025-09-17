import streamlit as st
import requests
import json
import hashlib
import secrets
from typing import Optional, Dict, Any
from database import DatabaseManager, User
import os
from datetime import datetime

class AuthManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.session_key = "user_session"
    
    def init_session_state(self):
        """Initialize session state for authentication"""
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None
        if 'is_authenticated' not in st.session_state:
            st.session_state.is_authenticated = False
    
    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user"""
        if st.session_state.is_authenticated and st.session_state.user_id:
            return self.db.get_user_by_id(st.session_state.user_id)
        return None
    
    def login_with_email(self, email: str, password: str) -> bool:
        """Login with email and password"""
        user = self.db.get_user_by_email(email)
        if not user:
            return False
        
        if user.auth_provider != 'email':
            return False
        
        # Verify password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        stored_hash = self._get_password_hash(user.id)
        
        if password_hash != stored_hash:
            return False
        
        self._set_user_session(user)
        return True
    
    def register_with_email(self, email: str, username: str, password: str, profile_data: Dict = None) -> bool:
        """Register with email and password"""
        try:
            # Check if user already exists
            existing_user = self.db.get_user_by_email(email)
            if existing_user:
                return False
            
            # Create new user
            user = self.db.create_user(
                email=email,
                username=username,
                auth_provider='email',
                password=password,
                profile_data=profile_data
            )
            
            if user:
                self._set_user_session(user)
                return True
            return False
        except Exception as e:
            st.error(f"Registration failed: {str(e)}")
            return False
    
    def login_with_google(self, google_token: str) -> bool:
        """Login with Google OAuth"""
        try:
            # Verify Google token
            user_info = self._verify_google_token(google_token)
            if not user_info:
                return False
            
            # Check if user exists
            user = self.db.get_user_by_email(user_info['email'])
            if not user:
                # Create new user
                user = self.db.create_user(
                    email=user_info['email'],
                    username=user_info.get('name', user_info['email'].split('@')[0]),
                    auth_provider='google',
                    auth_id=user_info['id'],
                    profile_data={
                        'name': user_info.get('name'),
                        'picture': user_info.get('picture'),
                        'locale': user_info.get('locale')
                    }
                )
            
            self._set_user_session(user)
            return True
        except Exception as e:
            st.error(f"Google login failed: {str(e)}")
            return False
    
    def login_with_facebook(self, facebook_token: str) -> bool:
        """Login with Facebook OAuth"""
        try:
            # Verify Facebook token
            user_info = self._verify_facebook_token(facebook_token)
            if not user_info:
                return False
            
            # Check if user exists
            user = self.db.get_user_by_email(user_info['email'])
            if not user:
                # Create new user
                user = self.db.create_user(
                    email=user_info['email'],
                    username=user_info.get('name', user_info['email'].split('@')[0]),
                    auth_provider='facebook',
                    auth_id=user_info['id'],
                    profile_data={
                        'name': user_info.get('name'),
                        'picture': user_info.get('picture', {}).get('data', {}).get('url'),
                        'locale': user_info.get('locale')
                    }
                )
            
            self._set_user_session(user)
            return True
        except Exception as e:
            st.error(f"Facebook login failed: {str(e)}")
            return False
    
    def logout(self):
        """Logout current user"""
        st.session_state.user_id = None
        st.session_state.user_data = None
        st.session_state.is_authenticated = False
        st.rerun()
    
    def _set_user_session(self, user: User):
        """Set user session data"""
        st.session_state.user_id = user.id
        st.session_state.user_data = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'auth_provider': user.auth_provider,
            'profile_data': user.profile_data,
            'preferences': user.preferences,
            'cooking_skill': user.cooking_skill,
            'achievements': user.achievements
        }
        st.session_state.is_authenticated = True
        
        # Update last login
        self._update_last_login(user.id)
    
    def _update_last_login(self, user_id: int):
        """Update user's last login time"""
        conn = self.db.db_path
        import sqlite3
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
    
    def _get_password_hash(self, user_id: int) -> Optional[str]:
        """Get user's password hash"""
        conn = self.db.db_path
        import sqlite3
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    def _verify_google_token(self, token: str) -> Optional[Dict]:
        """Verify Google OAuth token"""
        try:
            response = requests.get(
                f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={token}"
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
    
    def _verify_facebook_token(self, token: str) -> Optional[Dict]:
        """Verify Facebook OAuth token"""
        try:
            response = requests.get(
                f"https://graph.facebook.com/me?fields=id,name,email,picture&access_token={token}"
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

def render_auth_ui(auth_manager: AuthManager, lang: str = "en"):
    """Render authentication UI"""
    st.title("🔐 Welcome to AI Meal Planner")
    st.markdown("Sign in to access your personalized meal planning experience")
    
    tab1, tab2, tab3 = st.tabs(["Sign In", "Sign Up", "Social Login"])
    
    with tab1:
        st.subheader("Sign In")
        with st.form("signin_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In")
            
            if submit:
                if auth_manager.login_with_email(email, password):
                    st.success("Successfully signed in!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
    
    with tab2:
        st.subheader("Sign Up")
        with st.form("signup_form"):
            email = st.text_input("Email", placeholder="your@email.com", key="signup_email")
            username = st.text_input("Username", placeholder="Choose a username", key="signup_username")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
            
            # Profile data
            st.markdown("**Profile Information**")
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("Age", min_value=14, max_value=90, value=28)
                height = st.number_input("Height (cm)", min_value=130, max_value=220, value=178)
            with col2:
                weight = st.number_input("Weight (kg)", min_value=35.0, max_value=250.0, value=78.0)
                gender = st.selectbox("Gender", ["Male", "Female"])
            
            cooking_skill = st.selectbox("Cooking Skill Level", 
                                       ["Beginner", "Intermediate", "Advanced"])
            
            submit = st.form_submit_button("Sign Up")
            
            if submit:
                if password != confirm_password:
                    st.error("Passwords don't match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    profile_data = {
                        'age': age,
                        'height': height,
                        'weight': weight,
                        'gender': gender,
                        'cooking_skill': cooking_skill.lower()
                    }
                    
                    if auth_manager.register_with_email(email, username, password, profile_data):
                        st.success("Account created successfully!")
                        st.rerun()
                    else:
                        st.error("Email already exists or registration failed")
    
    with tab3:
        st.subheader("Social Login")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Google")
            st.markdown("Sign in with your Google account")
            if st.button("Sign in with Google", key="google_login"):
                st.info("Google OAuth integration would be implemented here")
                st.code("""
                # In production, this would redirect to Google OAuth
                # For demo purposes, we'll simulate a successful login
                """)
        
        with col2:
            st.markdown("### Facebook")
            st.markdown("Sign in with your Facebook account")
            if st.button("Sign in with Facebook", key="facebook_login"):
                st.info("Facebook OAuth integration would be implemented here")
                st.code("""
                # In production, this would redirect to Facebook OAuth
                # For demo purposes, we'll simulate a successful login
                """)

def require_auth(auth_manager: AuthManager):
    """Decorator to require authentication for certain functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.is_authenticated:
                st.warning("Please sign in to access this feature")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator
