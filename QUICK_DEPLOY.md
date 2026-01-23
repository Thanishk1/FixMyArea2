# Quick Deployment Guide

## 🚀 Fastest Way: Railway (Recommended)

### Step 1: Prepare Your Code
1. Make sure all files are committed to Git
2. Your code is ready - we've already set it up!

### Step 2: Deploy to Railway
1. Go to https://railway.app and sign up (free)
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your GitHub repository
4. Railway will automatically detect Django

### Step 3: Add Database
1. In Railway dashboard, click "New" → "Database" → "PostgreSQL"
2. Railway will automatically set database environment variables

### Step 4: Set Environment Variables
In Railway, go to your app → Variables tab, add:
```
SECRET_KEY=<generate one using: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DEBUG=False
ALLOWED_HOSTS=*.railway.app
```

### Step 5: Deploy!
Railway will automatically:
- Install dependencies from requirements.txt
- Run migrations
- Start your app

### Step 6: Run Setup Commands
In Railway dashboard → your app → Deployments → click the deployment → "View Logs" → "Run Command":
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py create_categories
python manage.py import_corporators --csv gwmc_corporators_clean.csv
```

## ✅ That's it! Your site is live!

Your website will be available at: `https://your-app-name.railway.app`

---

## Alternative: Render.com (Also Free)

1. Go to https://render.com
2. Sign up and create a "Web Service"
3. Connect your GitHub repo
4. Use these settings:
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn civic.wsgi`
5. Add PostgreSQL database
6. Set environment variables (same as Railway)
7. Deploy!

---

## Need Help?

Check `DEPLOYMENT.md` for detailed instructions for other platforms.
