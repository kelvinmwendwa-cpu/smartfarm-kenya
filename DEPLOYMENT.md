# SmartFarm Kenya - Deployment Guide

Complete guide for hosting SmartFarm Kenya online.

## Quick Deployment Options

### 1. Heroku (Recommended for Beginners)
```bash
# Install Heroku CLI
npm install -g heroku

# Login
heroku login

# Create app
heroku create smartfarm-kenya

# Deploy
git init
git add .
git commit -m "Deploy SmartFarm Kenya"
heroku git:remote -a heroku https://git.heroku.com/smartfarm-kenya.git
git push heroku main

# Set environment variables
heroku config:set SECRET_KEY=your-production-secret-key
heroku config:set WEATHER_API_KEY=your-openweather-api-key
```

### 2. PythonAnywhere (Free Option)
```bash
# Install
pip install pythonanywhere

# Deploy
pythonanywhere --set-port 5000 app.py
```

### 3. Vercel (Modern Option)
```bash
# Install Vercel
npm install -g vercel

# Deploy
vercel --prod
```

### 4. Railway (Easy Deployment)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### 5. DigitalOcean App Platform
```bash
# Using web interface
1. Go to app.digitalocean.com
2. Connect your GitHub repository
3. Configure build and deployment
4. Deploy with automatic SSL
```

## Pre-Deployment Checklist

### ✅ Required Files
- [x] `app.py` - Main Flask application
- [x] `requirements.txt` - Python dependencies
- [x] `wsgi.py` - WSGI entry point
- [x] `Procfile` - Process configuration
- [x] `runtime.txt` - Python version specification
- [x] `.env` - Environment variables (create from .env.example)

### ✅ Environment Setup
- [x] Install all dependencies: `pip install -r requirements.txt`
- [x] Set production secret key
- [x] Configure weather API key
- [x] Test all features locally

### ✅ Database Setup
- [x] SQLite database will be created automatically
- [x] Admin user will be created on first run
- [x] All tables will be initialized

## Environment Variables

Create `.env` file for production:
```env
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key-here
DATABASE_URL=sqlite:///smartfarm_kenya.db
WEATHER_API_KEY=your-openweather-api-key-here
```

## Deployment Commands

### Heroku Deployment
```bash
# 1. Prepare your code
git init
git add .
git commit -m "Ready for deployment"

# 2. Create Heroku app
heroku create smartfarm-kenya

# 3. Set environment variables
heroku config:set SECRET_KEY=your-production-secret-key
heroku config:set WEATHER_API_KEY=your-openweather-api-key

# 4. Deploy
heroku git:remote -a heroku https://git.heroku.com/smartfarm-kenya.git
git push heroku main

# 5. Open your app
heroku open
```

### PythonAnywhere Deployment
```bash
# 1. Install PythonAnywhere
pip install pythonanywhere

# 2. Deploy
pythonanywhere --set-port 5000 app.py

# 3. Get your URL
pythonanywhere list
```

### Vercel Deployment
```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy
vercel --prod

# 3. Your app will be live at: https://your-app-name.vercel.app
```

## Post-Deployment

### ✅ Testing Checklist
- [ ] Admin login works (username: admin, password: admin123)
- [ ] Farmer registration works
- [ ] Weather system loads all 47 counties
- [ ] AI assistant provides diagnosis
- [ ] All forms submit without errors
- [ ] Mobile responsive design works
- [ ] Database operations work correctly

### ✅ Production Settings
- [ ] Update SECRET_KEY to a secure value
- [ ] Configure proper domain name
- [ ] Set up SSL certificate (usually automatic)
- [ ] Monitor application logs
- [ ] Set up backup strategy

## Features Ready for Production

### 🛡️ Admin System
- Member management with statistics
- Crop information management
- Market price updates
- Farmer alert system
- CSRF protection on all forms

### 🌾 Farmer Portal
- User registration and login
- Crop and livestock tracking
- 47-county weather system
- AI-powered diagnosis
- Activity logging
- Photo gallery

### 📱 Professional Interface
- Unified dropdown navigation
- Mobile-responsive design
- Modern card-based layouts
- Consistent green theme
- Bootstrap 5 styling

## Support

For deployment issues:
1. Check logs: `heroku logs --tail` for Heroku
2. Verify environment variables
3. Test all features after deployment
4. Monitor database performance

## Security Notes

- Change default admin password in production
- Use HTTPS for all deployed applications
- Keep API keys secure
- Regularly update dependencies
- Monitor for suspicious activity

---

**Your SmartFarm Kenya application is ready for online deployment!** 🌱🇰🇪🚀
