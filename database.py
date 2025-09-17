import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib
import secrets

@dataclass
class User:
    id: int
    email: str
    username: str
    auth_provider: str  # 'email', 'google', 'facebook'
    created_at: datetime
    last_login: datetime
    profile_data: Dict
    preferences: Dict
    cooking_skill: str  # 'beginner', 'intermediate', 'advanced'
    achievements: List[str]
    friends: List[int]
    is_active: bool = True

@dataclass
class NutritionReport:
    user_id: int
    week_start: datetime
    total_calories: int
    avg_daily_calories: int
    protein_avg: float
    carbs_avg: float
    fat_avg: float
    weight_change: float
    goals_met: Dict
    recommendations: List[str]
    created_at: datetime

@dataclass
class Achievement:
    id: str
    name: str
    description: str
    icon: str
    category: str  # 'consistency', 'nutrition', 'social', 'cooking'
    requirements: Dict

@dataclass
class CommunityChallenge:
    id: str
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    participants: List[int]
    rewards: Dict
    is_active: bool = True

class DatabaseManager:
    def __init__(self, db_path: str = "meal_planner.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                auth_provider TEXT NOT NULL,
                auth_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                profile_data TEXT,
                preferences TEXT,
                cooking_skill TEXT DEFAULT 'beginner',
                achievements TEXT DEFAULT '[]',
                friends TEXT DEFAULT '[]',
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Nutrition reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nutrition_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                week_start TIMESTAMP NOT NULL,
                total_calories INTEGER,
                avg_daily_calories INTEGER,
                protein_avg REAL,
                carbs_avg REAL,
                fat_avg REAL,
                weight_change REAL,
                goals_met TEXT,
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User preferences learning table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                food_item TEXT NOT NULL,
                rating INTEGER NOT NULL,
                meal_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Meal plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meal_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_data TEXT NOT NULL,
                week_start TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Progress tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TIMESTAMP NOT NULL,
                weight REAL,
                body_fat REAL,
                measurements TEXT,
                photos TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Community challenges table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_challenges (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                participants TEXT DEFAULT '[]',
                rewards TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User challenges participation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                challenge_id TEXT NOT NULL,
                progress_data TEXT,
                completed BOOLEAN DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (challenge_id) REFERENCES community_challenges (id)
            )
        ''')
        
        # Food recognition logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS food_recognition_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                image_path TEXT,
                recognized_foods TEXT,
                confidence_scores TEXT,
                meal_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Analytics events
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT NOT NULL,
                event_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        self._init_default_data()
    
    def _init_default_data(self):
        """Initialize default achievements and challenges"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Default achievements
        achievements = [
            {
                'id': 'first_week',
                'name': 'First Week Complete',
                'description': 'Completed your first week of meal planning',
                'icon': '🎉',
                'category': 'consistency',
                'requirements': {'weeks_completed': 1}
            },
            {
                'id': 'protein_master',
                'name': 'Protein Master',
                'description': 'Met protein goals for 7 consecutive days',
                'icon': '💪',
                'category': 'nutrition',
                'requirements': {'protein_days': 7}
            },
            {
                'id': 'meal_prep_pro',
                'name': 'Meal Prep Pro',
                'description': 'Generated 10 meal plans',
                'icon': '🍽️',
                'category': 'cooking',
                'requirements': {'meal_plans': 10}
            },
            {
                'id': 'social_butterfly',
                'name': 'Social Butterfly',
                'description': 'Shared progress with 5 friends',
                'icon': '🦋',
                'category': 'social',
                'requirements': {'shared_progress': 5}
            }
        ]
        
        # Insert default achievements (if not exists)
        for achievement in achievements:
            cursor.execute('''
                INSERT OR IGNORE INTO achievements (id, name, description, icon, category, requirements)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                achievement['id'],
                achievement['name'],
                achievement['description'],
                achievement['icon'],
                achievement['category'],
                json.dumps(achievement['requirements'])
            ))
        
        conn.commit()
        conn.close()
    
    def create_user(self, email: str, username: str, auth_provider: str, 
                   auth_id: str = None, password: str = None, profile_data: Dict = None) -> User:
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = None
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO users (email, username, password_hash, auth_provider, auth_id, profile_data, preferences)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            email, username, password_hash, auth_provider, auth_id,
            json.dumps(profile_data or {}),
            json.dumps({'dietary_restrictions': [], 'favorite_cuisines': [], 'disliked_foods': []})
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return self.get_user_by_id(user_id)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return User(
            id=row[0],
            email=row[1],
            username=row[2],
            auth_provider=row[4],
            created_at=datetime.fromisoformat(row[6]),
            last_login=datetime.fromisoformat(row[7]),
            profile_data=json.loads(row[8] or '{}'),
            preferences=json.loads(row[9] or '{}'),
            cooking_skill=row[10] or 'beginner',
            achievements=json.loads(row[11] or '[]'),
            friends=json.loads(row[12] or '[]'),
            is_active=bool(row[13])
        )
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return User(
            id=row[0],
            email=row[1],
            username=row[2],
            auth_provider=row[4],
            created_at=datetime.fromisoformat(row[6]),
            last_login=datetime.fromisoformat(row[7]),
            profile_data=json.loads(row[8] or '{}'),
            preferences=json.loads(row[9] or '{}'),
            cooking_skill=row[10] or 'beginner',
            achievements=json.loads(row[11] or '[]'),
            friends=json.loads(row[12] or '[]'),
            is_active=bool(row[13])
        )
    
    def update_user_preferences(self, user_id: int, food_item: str, rating: int, meal_type: str = None):
        """Update user food preferences based on ratings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_preferences (user_id, food_item, rating, meal_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, food_item, rating, meal_type))
        
        conn.commit()
        conn.close()
    
    def get_user_preferences(self, user_id: int) -> Dict:
        """Get user's learned food preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT food_item, AVG(rating) as avg_rating, COUNT(*) as count
            FROM user_preferences 
            WHERE user_id = ?
            GROUP BY food_item
            ORDER BY avg_rating DESC
        ''', (user_id,))
        
        preferences = {}
        for row in cursor.fetchall():
            preferences[row[0]] = {
                'avg_rating': row[1],
                'count': row[2]
            }
        
        conn.close()
        return preferences
    
    def save_meal_plan(self, user_id: int, plan_data: Dict, week_start: datetime):
        """Save user's meal plan"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO meal_plans (user_id, plan_data, week_start)
            VALUES (?, ?, ?)
        ''', (user_id, json.dumps(plan_data), week_start))
        
        conn.commit()
        conn.close()
    
    def get_meal_plans(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's meal plans"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT plan_data, week_start, created_at
            FROM meal_plans 
            WHERE user_id = ?
            ORDER BY week_start DESC
            LIMIT ?
        ''', (user_id, limit))
        
        plans = []
        for row in cursor.fetchall():
            plans.append({
                'plan_data': json.loads(row[0]),
                'week_start': datetime.fromisoformat(row[1]),
                'created_at': datetime.fromisoformat(row[2])
            })
        
        conn.close()
        return plans
    
    def create_nutrition_report(self, user_id: int, week_start: datetime, 
                              nutrition_data: Dict, recommendations: List[str]) -> NutritionReport:
        """Create a weekly nutrition report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO nutrition_reports 
            (user_id, week_start, total_calories, avg_daily_calories, 
             protein_avg, carbs_avg, fat_avg, weight_change, goals_met, recommendations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, week_start,
            nutrition_data.get('total_calories', 0),
            nutrition_data.get('avg_daily_calories', 0),
            nutrition_data.get('protein_avg', 0),
            nutrition_data.get('carbs_avg', 0),
            nutrition_data.get('fat_avg', 0),
            nutrition_data.get('weight_change', 0),
            json.dumps(nutrition_data.get('goals_met', {})),
            json.dumps(recommendations)
        ))
        
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return NutritionReport(
            user_id=user_id,
            week_start=week_start,
            total_calories=nutrition_data.get('total_calories', 0),
            avg_daily_calories=nutrition_data.get('avg_daily_calories', 0),
            protein_avg=nutrition_data.get('protein_avg', 0),
            carbs_avg=nutrition_data.get('carbs_avg', 0),
            fat_avg=nutrition_data.get('fat_avg', 0),
            weight_change=nutrition_data.get('weight_change', 0),
            goals_met=nutrition_data.get('goals_met', {}),
            recommendations=recommendations,
            created_at=datetime.now()
        )
    
    def get_nutrition_reports(self, user_id: int, limit: int = 12) -> List[NutritionReport]:
        """Get user's nutrition reports"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM nutrition_reports 
            WHERE user_id = ?
            ORDER BY week_start DESC
            LIMIT ?
        ''', (user_id, limit))
        
        reports = []
        for row in cursor.fetchall():
            reports.append(NutritionReport(
                user_id=row[1],
                week_start=datetime.fromisoformat(row[2]),
                total_calories=row[3],
                avg_daily_calories=row[4],
                protein_avg=row[5],
                carbs_avg=row[6],
                fat_avg=row[7],
                weight_change=row[8],
                goals_met=json.loads(row[9] or '{}'),
                recommendations=json.loads(row[10] or '[]'),
                created_at=datetime.fromisoformat(row[11])
            ))
        
        conn.close()
        return reports
    
    def log_analytics_event(self, user_id: int, event_type: str, event_data: Dict = None):
        """Log analytics event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analytics_events (user_id, event_type, event_data)
            VALUES (?, ?, ?)
        ''', (user_id, event_type, json.dumps(event_data or {})))
        
        conn.commit()
        conn.close()
    
    def get_analytics_data(self, user_id: int, days: int = 30) -> Dict:
        """Get analytics data for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT event_type, COUNT(*) as count
            FROM analytics_events 
            WHERE user_id = ? AND created_at >= ?
            GROUP BY event_type
        ''', (user_id, start_date))
        
        events = {}
        for row in cursor.fetchall():
            events[row[0]] = row[1]
        
        conn.close()
        return events
