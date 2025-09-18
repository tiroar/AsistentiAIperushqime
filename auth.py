import streamlit as st
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
    

def render_auth_ui(auth_manager: AuthManager, lang: str = "en"):
    """Render authentication UI"""
    if lang == "sq":
        st.title("🔐 Mirë se vini në Asistentin e Ushqimeve AI")
        st.markdown("Kyçuni për të aksesuar përvojën tuaj të personalizuar të planifikimit të ushqimeve")
        st.markdown("*Ju mund të regjistroheni me çfardo emaili, nuk ka nevojë për verifikim*")
        
        
        tab1, tab2 = st.tabs(["Kyçuni", "Regjistrohuni"])
    else:
        st.title("🔐 Mirë se vini në Asistentin e Ushqimeve AI")
        st.markdown("Kyçuni për të aksesuar përvojën tuaj të personalizuar të planifikimit të ushqimeve")
        
        
        tab1, tab2 = st.tabs(["Kyçuni", "Regjistrohuni"])
    
    with tab1:
        if lang == "sq":
            st.subheader("Kyçuni")
            with st.form("signin_form"):
                email = st.text_input("Email", placeholder="email@juaj.com")
                password = st.text_input("Fjalëkalimi", type="password")
                submit = st.form_submit_button("Kyçuni")
                
                if submit:
                    if auth_manager.login_with_email(email, password):
                        st.success("U kyçët me sukses!")
                        st.rerun()
                    else:
                        st.error("Email ose fjalëkalim i pasaktë")
        else:
            st.subheader("Kyçuni")
            with st.form("signin_form"):
                email = st.text_input("Email", placeholder="email@juaj.com")
                password = st.text_input("Fjalëkalimi", type="password")
                submit = st.form_submit_button("Kyçuni")
                
                if submit:
                    if auth_manager.login_with_email(email, password):
                        st.success("U kyçët me sukses!")
                        st.rerun()
                    else:
                        st.error("Email ose fjalëkalim i pasaktë")
    
    with tab2:
        if lang == "sq":
            st.subheader("Regjistrohuni")
            with st.form("signup_form"):
                email = st.text_input("Email", placeholder="email@juaj.com", key="signup_email")
                username = st.text_input("Emri i Përdoruesit", placeholder="Zgjidhni një emër përdoruesi", key="signup_username")
                password = st.text_input("Fjalëkalimi", type="password", key="signup_password")
                confirm_password = st.text_input("Konfirmoni Fjalëkalimin", type="password", key="signup_confirm")
                
                # Profile data
                st.markdown("**Informacioni i Profilit**")
                col1, col2 = st.columns(2)
                with col1:
                    age = st.number_input("Mosha", min_value=14, max_value=90, value=28)
                    height = st.number_input("Gjatësia (cm)", min_value=130, max_value=220, value=178)
                with col2:
                    weight = st.number_input("Pesha (kg)", min_value=35.0, max_value=250.0, value=78.0)
                    gender = st.selectbox("Gjinia", ["Mashkull", "Femër"])
                
                cooking_skill = st.selectbox("Niveli i Gatimit", 
                                           ["Fillestar", "Mesatar", "I Avancuar"])
                
                submit = st.form_submit_button("Regjistrohuni")
                
                if submit:
                    if password != confirm_password:
                        st.error("Fjalëkalimet nuk përputhen")
                    elif len(password) < 6:
                        st.error("Fjalëkalimi duhet të jetë të paktën 6 karaktere")
                    else:
                        profile_data = {
                            'age': age,
                            'height': height,
                            'weight': weight,
                            'gender': gender,
                            'cooking_skill': cooking_skill.lower()
                        }
                        
                        if auth_manager.register_with_email(email, username, password, profile_data):
                            st.success("Llogaria u krijua me sukses!")
                            st.rerun()
                        else:
                            st.error("Email ekziston tashmë ose regjistrimi dështoi")
        else:
            st.subheader("Regjistrohuni")
            with st.form("signup_form"):
                email = st.text_input("Email", placeholder="email@juaj.com", key="signup_email")
                username = st.text_input("Emri i Përdoruesit", placeholder="Zgjidhni një emër përdoruesi", key="signup_username")
                password = st.text_input("Fjalëkalimi", type="password", key="signup_password")
                confirm_password = st.text_input("Konfirmoni Fjalëkalimin", type="password", key="signup_confirm")
                
                # Profile data
                st.markdown("**Informacioni i Profilit**")
                col1, col2 = st.columns(2)
                with col1:
                    age = st.number_input("Mosha", min_value=14, max_value=90, value=28)
                    height = st.number_input("Gjatësia (cm)", min_value=130, max_value=220, value=178)
                with col2:
                    weight = st.number_input("Pesha (kg)", min_value=35.0, max_value=250.0, value=78.0)
                    gender = st.selectbox("Gjinia", ["Mashkull", "Femër"])
                
                cooking_skill = st.selectbox("Niveli i Gatimit", 
                                           ["Fillestar", "Mesatar", "I Avancuar"])
                
                submit = st.form_submit_button("Regjistrohuni")
                
                if submit:
                    if password != confirm_password:
                        st.error("Fjalëkalimet nuk përputhen")
                    elif len(password) < 6:
                        st.error("Fjalëkalimi duhet të jetë të paktën 6 karaktere")
                    else:
                        profile_data = {
                            'age': age,
                            'height': height,
                            'weight': weight,
                            'gender': gender,
                            'cooking_skill': cooking_skill.lower()
                        }
                        
                        if auth_manager.register_with_email(email, username, password, profile_data):
                            st.success("Llogaria u krijua me sukses!")
                            st.rerun()
                        else:
                            st.error("Email ekziston tashmë ose regjistrimi dështoi")
    

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
