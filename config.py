import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Database Configuration
    DATABASE_PATH = os.getenv("DATABASE_PATH", "meal_planner.db")
    
    # Social Login Configuration
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "")
    FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
    
    # App Configuration
    APP_NAME = os.getenv("APP_NAME", "AI Meal Planner")
    APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Feature Flags
    ENABLE_IMAGE_RECOGNITION = True
    ENABLE_SOCIAL_FEATURES = True
    ENABLE_ANALYTICS = True
    ENABLE_PREFERENCE_LEARNING = True
    
    # Default Values
    DEFAULT_COOKING_SKILL = "beginner"
    DEFAULT_MEAL_PATTERN = "30/40/30"
    DEFAULT_CALORIE_TARGET = 2000
    
    # Achievement Settings
    ACHIEVEMENT_REQUIREMENTS = {
        'first_week': {'weeks_completed': 1},
        'protein_master': {'protein_days': 7},
        'meal_prep_pro': {'meal_plans': 10},
        'social_butterfly': {'shared_progress': 5}
    }
    
    # Community Challenge Settings
    CHALLENGE_DURATION_DAYS = 7
    MAX_CHALLENGE_PARTICIPANTS = 100
    
    # Analytics Settings
    ANALYTICS_RETENTION_DAYS = 365
    NUTRITION_REPORT_RETENTION_WEEKS = 52
    
    # Image Recognition Settings
    MAX_IMAGE_SIZE_MB = 10
    SUPPORTED_IMAGE_FORMATS = ['png', 'jpg', 'jpeg']
    
    # Preference Learning Settings
    MIN_RATINGS_FOR_LEARNING = 5
    PREFERENCE_CONFIDENCE_THRESHOLD = 0.7
    
    # Cooking Skill Settings
    SKILL_LEVELS = ['beginner', 'intermediate', 'advanced']
    SKILL_ADAPTATION_ENABLED = True
    
    # Social Features Settings
    MAX_FRIENDS = 100
    PROGRESS_SHARING_ENABLED = True
    ACHIEVEMENT_NOTIFICATIONS = True
    
    # Database Settings
    DATABASE_BACKUP_ENABLED = True
    DATABASE_BACKUP_FREQUENCY_HOURS = 24
    
    # Security Settings
    PASSWORD_MIN_LENGTH = 6
    SESSION_TIMEOUT_HOURS = 24
    MAX_LOGIN_ATTEMPTS = 5
    
    # Performance Settings
    CACHE_TTL_SECONDS = 3600
    MAX_CONCURRENT_USERS = 100
    REQUEST_TIMEOUT_SECONDS = 30
    
    # Localization Settings
    DEFAULT_LANGUAGE = "en"
    SUPPORTED_LANGUAGES = ["en", "sq"]  # English, Albanian
    TRANSLATION_ENABLED = True
    
    # Export Settings
    MAX_EXPORT_RECORDS = 1000
    EXPORT_FORMATS = ["csv", "json", "pdf"]
    
    # Notification Settings
    EMAIL_NOTIFICATIONS = False
    PUSH_NOTIFICATIONS = False
    WEEKLY_REMINDERS = True
    
    # AI Settings
    AI_TEMPERATURE = 0.2
    AI_MAX_TOKENS = 1000
    AI_MODEL = "gpt-4o-mini"
    
    # Recipe Settings
    MAX_RECIPES_PER_PLAN = 21  # 7 days * 3 meals
    MIN_RECIPE_RATING = 1
    MAX_RECIPE_RATING = 5
    
    # Nutrition Settings
    MIN_CALORIES_PER_MEAL = 100
    MAX_CALORIES_PER_MEAL = 1000
    MACRO_TOLERANCE_PERCENT = 10
    
    # Shopping List Settings
    GROUP_INGREDIENTS = True
    SORT_BY_CATEGORY = True
    INCLUDE_QUANTITIES = True
    
    # Meal Planning Settings
    DIVERSITY_PENALTY = 0.8
    PREFERENCE_BONUS = 0.3
    CALORIE_TOLERANCE = 50
    
    # User Experience Settings
    SHOW_TIPS = True
    ENABLE_TOUR = True
    SAVE_USER_PREFERENCES = True
    
    # Development Settings
    LOG_LEVEL = "INFO"
    ENABLE_DEBUG_MODE = DEBUG
    MOCK_EXTERNAL_APIS = False
    
    # Monitoring Settings
    ENABLE_METRICS = True
    METRICS_RETENTION_DAYS = 30
    ERROR_REPORTING = True
    
    # Backup Settings
    BACKUP_TO_CLOUD = False
    BACKUP_ENCRYPTION = True
    BACKUP_COMPRESSION = True
    
    # Integration Settings
    ENABLE_WEBHOOKS = False
    WEBHOOK_TIMEOUT_SECONDS = 10
    MAX_WEBHOOK_RETRIES = 3
    
    # Content Settings
    MAX_CONTENT_LENGTH = 10000
    ENABLE_CONTENT_FILTERING = True
    ALLOW_USER_GENERATED_CONTENT = True
    
    # Privacy Settings
    COLLECT_ANALYTICS = True
    ANONYMIZE_DATA = True
    DATA_RETENTION_DAYS = 365
    GDPR_COMPLIANCE = True
    
    # Performance Optimization
    ENABLE_CACHING = True
    CACHE_SIZE_MB = 100
    ENABLE_COMPRESSION = True
    OPTIMIZE_IMAGES = True
    
    # Error Handling
    MAX_ERROR_RETRIES = 3
    ERROR_COOLDOWN_SECONDS = 60
    GRACEFUL_DEGRADATION = True
    
    # Testing Settings
    ENABLE_TEST_MODE = False
    MOCK_DATABASE = False
    TEST_USER_ID = 1
    
    # Deployment Settings
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    HOST = os.getenv("HOST", "localhost")
    PORT = int(os.getenv("PORT", "8501"))
    
    # Logging Settings
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "app.log"
    LOG_MAX_SIZE_MB = 10
    LOG_BACKUP_COUNT = 5
    
    # Security Headers
    ENABLE_CORS = True
    CORS_ORIGINS = ["*"]
    ENABLE_CSRF_PROTECTION = True
    ENABLE_RATE_LIMITING = True
    
    # API Settings
    API_RATE_LIMIT = "100/hour"
    API_TIMEOUT_SECONDS = 30
    ENABLE_API_DOCUMENTATION = True
    
    # File Upload Settings
    MAX_FILE_SIZE_MB = 10
    ALLOWED_FILE_TYPES = ["png", "jpg", "jpeg", "pdf", "csv"]
    UPLOAD_FOLDER = "uploads"
    
    # Email Settings
    SMTP_SERVER = os.getenv("SMTP_SERVER", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "")
    
    # Social Media Settings
    ENABLE_SOCIAL_SHARING = True
    TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
    FACEBOOK_API_KEY = os.getenv("FACEBOOK_API_KEY", "")
    
    # Payment Settings (for future premium features)
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    ENABLE_PAYMENTS = False
    
    # Mobile App Settings
    ENABLE_PUSH_NOTIFICATIONS = False
    FIREBASE_SERVER_KEY = os.getenv("FIREBASE_SERVER_KEY", "")
    
    # Third-party Integrations
    ENABLE_GOOGLE_FIT = False
    ENABLE_APPLE_HEALTH = False
    ENABLE_MYFITNESSPAL = False
    
    # Advanced Features
    ENABLE_MACHINE_LEARNING = True
    ENABLE_RECOMMENDATION_ENGINE = True
    ENABLE_PREDICTIVE_ANALYTICS = True
    
    # Quality Assurance
    ENABLE_AUTOMATED_TESTING = False
    ENABLE_PERFORMANCE_MONITORING = True
    ENABLE_ERROR_TRACKING = True
    
    # Compliance
    ENABLE_AUDIT_LOGGING = True
    ENABLE_DATA_EXPORT = True
    ENABLE_DATA_DELETION = True
    
    # Scalability
    ENABLE_HORIZONTAL_SCALING = False
    ENABLE_LOAD_BALANCING = False
    ENABLE_DATABASE_SHARDING = False
    
    # Monitoring and Alerting
    ENABLE_HEALTH_CHECKS = True
    ENABLE_ALERTING = False
    ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")
    
    # Maintenance
    ENABLE_MAINTENANCE_MODE = False
    MAINTENANCE_MESSAGE = "The app is currently under maintenance. Please try again later."
    
    # Feature Rollouts
    ENABLE_BETA_FEATURES = False
    BETA_FEATURE_FLAGS = {
        'advanced_ai': False,
        'voice_commands': False,
        'ar_cooking': False,
        'smart_home_integration': False
    }
    
    # Internationalization
    ENABLE_I18N = True
    DEFAULT_TIMEZONE = "UTC"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"
    
    # Accessibility
    ENABLE_ACCESSIBILITY_FEATURES = True
    HIGH_CONTRAST_MODE = False
    SCREEN_READER_SUPPORT = True
    
    # Performance
    ENABLE_LAZY_LOADING = True
    ENABLE_IMAGE_OPTIMIZATION = True
    ENABLE_CDN = False
    
    # Security
    ENABLE_2FA = False
    ENABLE_BIOMETRIC_AUTH = False
    ENABLE_DEVICE_TRACKING = False
    
    # Data Processing
    ENABLE_BATCH_PROCESSING = True
    BATCH_SIZE = 100
    PROCESSING_INTERVAL_MINUTES = 5
    
    # Reporting
    ENABLE_AUTOMATED_REPORTS = True
    REPORT_SCHEDULE = "weekly"
    REPORT_RECIPIENTS = []
    
    # Integration Testing
    ENABLE_INTEGRATION_TESTS = False
    TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
    MOCK_EXTERNAL_SERVICES = True
