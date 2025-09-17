import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from database import DatabaseManager
import json
from datetime import datetime, timedelta
import random

class SocialFeatures:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_achievements(self, user_id: int) -> List[Dict]:
        """Get user's achievements"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return []
        
        return user.achievements
    
    def check_and_award_achievements(self, user_id: int, event_type: str, event_data: Dict = None):
        """Check and award achievements based on user activity"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return
        
        current_achievements = set(user.achievements)
        new_achievements = []
        
        # Check various achievement conditions
        if event_type == 'meal_plan_generated':
            # Check meal plan achievements
            meal_plans = self.db.get_meal_plans(user_id)
            if len(meal_plans) >= 1 and 'first_week' not in current_achievements:
                new_achievements.append('first_week')
            
            if len(meal_plans) >= 10 and 'meal_prep_pro' not in current_achievements:
                new_achievements.append('meal_prep_pro')
        
        elif event_type == 'nutrition_goal_met':
            # Check nutrition achievements
            if event_data and event_data.get('protein_goal_met'):
                # Check for consecutive protein goal days
                # This would require more complex tracking
                pass
        
        elif event_type == 'progress_shared':
            # Check social achievements
            if 'social_butterfly' not in current_achievements:
                new_achievements.append('social_butterfly')
        
        # Award new achievements
        if new_achievements:
            self._award_achievements(user_id, new_achievements)
    
    def _award_achievements(self, user_id: int, achievement_ids: List[str]):
        """Award achievements to user"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return
        
        current_achievements = user.achievements.copy()
        current_achievements.extend(achievement_ids)
        
        # Update user's achievements
        conn = self.db.db_path
        import sqlite3
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET achievements = ? WHERE id = ?
        ''', (json.dumps(current_achievements), user_id))
        
        conn.commit()
        conn.close()
        
        # Log analytics event
        self.db.log_analytics_event(
            user_id=user_id,
            event_type='achievement_awarded',
            event_data={'achievements': achievement_ids}
        )
    
    def get_community_challenges(self) -> List[Dict]:
        """Get active community challenges"""
        conn = self.db.db_path
        import sqlite3
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM community_challenges 
            WHERE is_active = 1 AND end_date > datetime('now')
            ORDER BY start_date DESC
        ''')
        
        challenges = []
        for row in cursor.fetchall():
            challenges.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'start_date': datetime.fromisoformat(row[3]),
                'end_date': datetime.fromisoformat(row[4]),
                'participants': json.loads(row[5] or '[]'),
                'rewards': json.loads(row[6] or '{}'),
                'is_active': bool(row[7])
            })
        
        conn.close()
        return challenges
    
    def join_challenge(self, user_id: int, challenge_id: str) -> bool:
        """Join a community challenge"""
        try:
            conn = self.db.db_path
            import sqlite3
            conn = sqlite3.connect(conn)
            cursor = conn.cursor()
            
            # Check if user is already in challenge
            cursor.execute('''
                SELECT id FROM user_challenges 
                WHERE user_id = ? AND challenge_id = ?
            ''', (user_id, challenge_id))
            
            if cursor.fetchone():
                conn.close()
                return False  # Already joined
            
            # Add user to challenge
            cursor.execute('''
                INSERT INTO user_challenges (user_id, challenge_id, progress_data)
                VALUES (?, ?, ?)
            ''', (user_id, challenge_id, json.dumps({})))
            
            # Update challenge participants
            cursor.execute('''
                SELECT participants FROM community_challenges WHERE id = ?
            ''', (challenge_id,))
            
            row = cursor.fetchone()
            if row:
                participants = json.loads(row[0] or '[]')
                if user_id not in participants:
                    participants.append(user_id)
                    cursor.execute('''
                        UPDATE community_challenges 
                        SET participants = ? WHERE id = ?
                    ''', (json.dumps(participants), challenge_id))
            
            conn.commit()
            conn.close()
            
            # Log analytics event
            self.db.log_analytics_event(
                user_id=user_id,
                event_type='challenge_joined',
                event_data={'challenge_id': challenge_id}
            )
            
            return True
        except Exception as e:
            st.error(f"Failed to join challenge: {str(e)}")
            return False
    
    def get_user_challenges(self, user_id: int) -> List[Dict]:
        """Get user's active challenges"""
        conn = self.db.db_path
        import sqlite3
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, uc.progress_data, uc.completed
            FROM community_challenges c
            JOIN user_challenges uc ON c.id = uc.challenge_id
            WHERE uc.user_id = ? AND c.is_active = 1
        ''', (user_id,))
        
        challenges = []
        for row in cursor.fetchall():
            challenges.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'start_date': datetime.fromisoformat(row[3]),
                'end_date': datetime.fromisoformat(row[4]),
                'participants': json.loads(row[5] or '[]'),
                'rewards': json.loads(row[6] or '{}'),
                'progress_data': json.loads(row[8] or '{}'),
                'completed': bool(row[9])
            })
        
        conn.close()
        return challenges
    
    def share_progress(self, user_id: int, progress_data: Dict) -> bool:
        """Share progress with friends"""
        try:
            # Log analytics event
            self.db.log_analytics_event(
                user_id=user_id,
                event_type='progress_shared',
                event_data=progress_data
            )
            
            # Check for social achievements
            self.check_and_award_achievements(user_id, 'progress_shared')
            
            return True
        except Exception as e:
            st.error(f"Failed to share progress: {str(e)}")
            return False
    
    def get_friends(self, user_id: int) -> List[Dict]:
        """Get user's friends"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return []
        
        friend_ids = user.friends
        friends = []
        
        for friend_id in friend_ids:
            friend = self.db.get_user_by_id(friend_id)
            if friend:
                friends.append({
                    'id': friend.id,
                    'username': friend.username,
                    'profile_data': friend.profile_data
                })
        
        return friends
    
    def add_friend(self, user_id: int, friend_username: str) -> bool:
        """Add a friend by username"""
        try:
            # Find friend by username
            conn = self.db.db_path
            import sqlite3
            conn = sqlite3.connect(conn)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE username = ?', (friend_username,))
            friend_row = cursor.fetchone()
            
            if not friend_row:
                conn.close()
                return False
            
            friend_id = friend_row[0]
            
            # Add friend to user's friends list
            user = self.db.get_user_by_id(user_id)
            if not user:
                conn.close()
                return False
            
            current_friends = user.friends.copy()
            if friend_id not in current_friends:
                current_friends.append(friend_id)
                
                cursor.execute('''
                    UPDATE users SET friends = ? WHERE id = ?
                ''', (json.dumps(current_friends), user_id))
                
                conn.commit()
            
            conn.close()
            return True
        except Exception as e:
            st.error(f"Failed to add friend: {str(e)}")
            return False

def render_social_features_ui(user_id: int, db_manager: DatabaseManager, lang: str = "en"):
    """Render social features UI"""
    st.title("👥 Social Features")
    
    social = SocialFeatures(db_manager)
    
    # Tabs for different social features
    tab1, tab2, tab3, tab4 = st.tabs(["Achievements", "Challenges", "Friends", "Share Progress"])
    
    with tab1:
        st.subheader("🏆 Your Achievements")
        
        achievements = social.get_achievements(user_id)
        
        if achievements:
            for achievement in achievements:
                st.success(f"✅ {achievement}")
        else:
            st.info("Complete some activities to earn achievements!")
        
        # Achievement categories
        st.subheader("Achievement Categories")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Consistency**")
            st.markdown("- First Week Complete")
            st.markdown("- 30-Day Streak")
            st.markdown("- Monthly Planner")
        
        with col2:
            st.markdown("**Nutrition**")
            st.markdown("- Protein Master")
            st.markdown("- Macro Perfect")
            st.markdown("- Healthy Eater")
    
    with tab2:
        st.subheader("🎯 Community Challenges")
        
        challenges = social.get_community_challenges()
        
        if challenges:
            for challenge in challenges:
                with st.expander(f"{challenge['name']} - {len(challenge['participants'])} participants"):
                    st.write(challenge['description'])
                    st.write(f"**Duration:** {challenge['start_date'].strftime('%Y-%m-%d')} to {challenge['end_date'].strftime('%Y-%m-%d')}")
                    
                    if st.button(f"Join {challenge['name']}", key=f"join_{challenge['id']}"):
                        if social.join_challenge(user_id, challenge['id']):
                            st.success("Successfully joined challenge!")
                            st.rerun()
                        else:
                            st.error("Failed to join challenge")
        else:
            st.info("No active challenges at the moment")
        
        # User's active challenges
        st.subheader("Your Active Challenges")
        
        user_challenges = social.get_user_challenges(user_id)
        
        if user_challenges:
            for challenge in user_challenges:
                st.write(f"**{challenge['name']}**")
                st.write(f"Progress: {challenge['progress_data']}")
                st.write(f"Status: {'Completed' if challenge['completed'] else 'In Progress'}")
        else:
            st.info("You're not participating in any challenges yet")
    
    with tab3:
        st.subheader("👫 Friends")
        
        friends = social.get_friends(user_id)
        
        if friends:
            for friend in friends:
                st.write(f"👤 {friend['username']}")
        else:
            st.info("Add some friends to share your progress!")
        
        # Add friend
        st.subheader("Add a Friend")
        
        with st.form("add_friend"):
            friend_username = st.text_input("Friend's Username", placeholder="Enter username")
            
            if st.form_submit_button("Add Friend"):
                if social.add_friend(user_id, friend_username):
                    st.success("Friend added successfully!")
                    st.rerun()
                else:
                    st.error("User not found or already added")
    
    with tab4:
        st.subheader("📤 Share Your Progress")
        
        # Get recent progress data
        recent_plans = db_manager.get_meal_plans(user_id, limit=1)
        
        if recent_plans:
            plan = recent_plans[0]
            
            st.write("**Recent Meal Plan:**")
            st.write(f"Week of {plan['week_start'].strftime('%Y-%m-%d')}")
            
            # Show plan summary
            plan_data = plan['plan_data']
            total_calories = 0
            
            for day, meals in plan_data.items():
                if isinstance(meals, dict):
                    day_calories = sum(
                        recipe.get('kcal', 0) for recipe in meals.values() 
                        if recipe and isinstance(recipe, dict)
                    )
                    total_calories += day_calories
            
            st.write(f"Total weekly calories: {total_calories:,}")
            
            # Share options
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Share on Social Media"):
                    st.info("Social media sharing would be implemented here")
            
            with col2:
                if st.button("Share with Friends"):
                    if social.share_progress(user_id, {
                        'plan_id': plan['id'],
                        'week_start': plan['week_start'].isoformat(),
                        'total_calories': total_calories
                    }):
                        st.success("Progress shared with friends!")
                    else:
                        st.error("Failed to share progress")
        else:
            st.info("Generate some meal plans first to share your progress!")
        
        # Progress sharing tips
        st.subheader("💡 Sharing Tips")
        st.markdown("""
        - Share your weekly meal plans to inspire others
        - Post your favorite recipes and cooking tips
        - Celebrate your achievements and milestones
        - Encourage friends on their fitness journey
        """)
