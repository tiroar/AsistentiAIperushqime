# AI Meal Planner - Enhanced Edition

A comprehensive AI-powered meal planning application designed specifically for weight loss goals, featuring advanced personalization, social features, and nutritionist-level intelligence.

## 🚀 New Features

### 🔐 User Authentication & Profiles
- **Multi-provider login**: Email/password, Google OAuth, Facebook OAuth
- **User profiles**: Personalized settings, preferences, and cooking skill levels
- **Secure session management**: Persistent login with automatic logout

### 📊 Advanced Analytics & Reporting
- **Weekly nutrition reports**: Comprehensive analysis of your eating habits
- **Progress tracking**: Visual charts and trends over time
- **Goal achievement monitoring**: Track your nutrition and fitness goals
- **Data export**: Download your data in CSV/JSON formats

### 🧠 AI-Powered Personalization
- **Food preference learning**: The app learns from your ratings and preferences
- **Smart recommendations**: Personalized recipe suggestions based on your history
- **Cooking skill adaptation**: Recipes adapt to your skill level (beginner/intermediate/advanced)
- **Intelligent substitutions**: AI suggests alternatives based on your pantry

### 👥 Social Features
- **Achievement system**: Unlock badges for milestones and consistency
- **Community challenges**: Participate in group fitness and nutrition challenges
- **Progress sharing**: Share your achievements with friends and family
- **Friend system**: Connect with others on their fitness journey

### 📸 Image Recognition
- **Food photo analysis**: Take photos of your meals for automatic nutrition tracking
- **AI-powered identification**: Recognizes food items and estimates portions
- **Nutrition estimation**: Automatically calculates calories and macros
- **Meal logging**: Easy way to track what you actually eat

### 🎯 Enhanced Meal Planning
- **Preference-based filtering**: Recipes filtered by your learned preferences
- **Cooking skill adaptation**: Instructions adapt to your skill level
- **Advanced AI generation**: More sophisticated recipe creation
- **Cultural adaptation**: Better support for Albanian and other cuisines

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- OpenAI API key (optional, for advanced AI features)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AsistentiAIperushqime
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your API keys
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the enhanced application**
   ```bash
   streamlit run app_enhanced.py
   ```

5. **Access the application**
   - Open your browser to `http://localhost:8501`
   - Create an account or sign in
   - Start planning your meals!

### Database Setup

The application automatically creates a SQLite database (`meal_planner.db`) on first run. No additional setup required.

## 📱 Features Overview

### 1. User Authentication
- **Sign Up**: Create account with email/password or social login
- **Profile Management**: Update personal information and preferences
- **Secure Login**: Persistent sessions with automatic logout

### 2. Meal Planning
- **Smart Planning**: AI generates 7-day meal plans based on your goals
- **Preference Learning**: App learns from your ratings and feedback
- **Skill Adaptation**: Recipes adapt to your cooking skill level
- **Cultural Support**: Full Albanian localization and Balkan cuisine

### 3. Nutrition Tracking
- **Weekly Reports**: Comprehensive nutrition analysis
- **Goal Monitoring**: Track progress toward your fitness goals
- **Trend Analysis**: Visual charts showing your progress over time
- **Export Data**: Download your nutrition data for external analysis

### 4. Social Features
- **Achievements**: Unlock badges for consistency and milestones
- **Challenges**: Join community fitness and nutrition challenges
- **Progress Sharing**: Share your achievements with friends
- **Friend System**: Connect with others on their fitness journey

### 5. Image Recognition
- **Food Photos**: Take photos of your meals for automatic tracking
- **AI Analysis**: Recognizes food items and estimates nutrition
- **Easy Logging**: Quick way to track what you actually eat
- **History Tracking**: View your food recognition history

### 6. Analytics Dashboard
- **Usage Insights**: Track your app usage and engagement
- **Performance Metrics**: Monitor your meal planning consistency
- **Data Visualization**: Charts and graphs of your progress
- **Export Options**: Download your data in various formats

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional - Social Login
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret

# Optional - Email Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Feature Flags

You can enable/disable features by modifying `config.py`:

```python
# Enable/disable features
ENABLE_IMAGE_RECOGNITION = True
ENABLE_SOCIAL_FEATURES = True
ENABLE_ANALYTICS = True
ENABLE_PREFERENCE_LEARNING = True
```

## 📊 Database Schema

The application uses SQLite with the following main tables:

- **users**: User profiles and authentication
- **meal_plans**: Generated meal plans
- **nutrition_reports**: Weekly nutrition analysis
- **user_preferences**: Learned food preferences
- **analytics_events**: User activity tracking
- **community_challenges**: Social challenges
- **food_recognition_logs**: Image recognition history

## 🚀 Deployment

### Local Development
```bash
streamlit run app_enhanced.py
```

### Production Deployment

1. **Using Streamlit Cloud**
   - Connect your GitHub repository
   - Set environment variables in the dashboard
   - Deploy automatically

2. **Using Docker**
   ```bash
   # Build the image
   docker build -t ai-meal-planner .
   
   # Run the container
   docker run -p 8501:8501 ai-meal-planner
   ```

3. **Using Heroku**
   ```bash
   # Install Heroku CLI
   # Create Procfile
   echo "web: streamlit run app_enhanced.py --server.port=$PORT --server.address=0.0.0.0" > Procfile
   
   # Deploy
   git push heroku main
   ```

## 🔒 Security Features

- **Password hashing**: Secure password storage
- **Session management**: Secure user sessions
- **Input validation**: Protection against malicious input
- **SQL injection prevention**: Parameterized queries
- **XSS protection**: Input sanitization
- **CSRF protection**: Cross-site request forgery prevention

## 📈 Performance Optimizations

- **Database indexing**: Optimized queries
- **Caching**: Reduced API calls and improved response times
- **Lazy loading**: Load data only when needed
- **Image optimization**: Compressed images for faster loading
- **Connection pooling**: Efficient database connections

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app_enhanced tests/
```

### Test Coverage
- Unit tests for all modules
- Integration tests for database operations
- API tests for external services
- UI tests for user interactions

## 📝 API Documentation

### Authentication Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/profile` - Get user profile

### Meal Planning Endpoints
- `POST /plans/generate` - Generate meal plan
- `GET /plans/history` - Get meal plan history
- `PUT /plans/{id}` - Update meal plan
- `DELETE /plans/{id}` - Delete meal plan

### Analytics Endpoints
- `GET /analytics/dashboard` - Get dashboard data
- `GET /analytics/reports` - Get nutrition reports
- `POST /analytics/export` - Export data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guide
- Write comprehensive tests
- Update documentation
- Use meaningful commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues

1. **Database errors**: Delete `meal_planner.db` and restart
2. **API key issues**: Check your OpenAI API key in `.env`
3. **Import errors**: Ensure all dependencies are installed
4. **Port conflicts**: Change the port in the command line

### Getting Help

- Check the documentation
- Search existing issues
- Create a new issue with detailed description
- Contact support at support@aimealplanner.com

## 🔮 Roadmap

### Upcoming Features
- [ ] Mobile app (React Native)
- [ ] Voice commands
- [ ] AR cooking assistance
- [ ] Smart home integration
- [ ] Advanced AI recommendations
- [ ] Meal prep scheduling
- [ ] Grocery delivery integration
- [ ] Fitness tracker integration

### Version History
- **v2.0.0**: Enhanced edition with all new features
- **v1.0.0**: Original meal planning app

## 🙏 Acknowledgments

- OpenAI for GPT-4 Vision API
- Streamlit for the web framework
- Plotly for data visualization
- The open-source community for various libraries

## 📞 Contact

- **Developer**: Your Name
- **Email**: your.email@example.com
- **GitHub**: https://github.com/yourusername
- **Website**: https://aimealplanner.com

---

**Made with ❤️ for healthy living and AI-powered nutrition**
