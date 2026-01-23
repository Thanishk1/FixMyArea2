# Deployment Guide for FixMyArea

This guide will help you deploy your FixMyArea website to the internet.

## Quick Deployment Options

### Option 1: Railway (Recommended - Easiest)

1. **Sign up** at [railway.app](https://railway.app)
2. **Create a new project**
3. **Connect your GitHub repository** (or deploy from local)
4. **Add PostgreSQL database**:
   - Click "New" → "Database" → "PostgreSQL"
5. **Set environment variables**:
   ```
   SECRET_KEY=your-secret-key-here (generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
   DEBUG=False
   ALLOWED_HOSTS=your-app-name.railway.app
   DB_NAME=railway
   DB_USER=postgres
   DB_PASSWORD=(from Railway dashboard)
   DB_HOST=(from Railway dashboard)
   DB_PORT=5432
   ```
6. **Deploy**: Railway will automatically detect Django and deploy

### Option 2: Heroku

1. **Install Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli
2. **Login**: `heroku login`
3. **Create app**: `heroku create fixmyarea`
4. **Add PostgreSQL**: `heroku addons:create heroku-postgresql:hobby-dev`
5. **Set environment variables**:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key-here
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS=fixmyarea.herokuapp.com
   ```
6. **Deploy**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   heroku git:remote -a fixmyarea
   git push heroku main
   ```
7. **Run migrations**: `heroku run python manage.py migrate`
8. **Create superuser**: `heroku run python manage.py createsuperuser`

### Option 3: DigitalOcean App Platform

1. **Sign up** at [digitalocean.com](https://www.digitalocean.com)
2. **Create App** → Connect GitHub repository
3. **Configure**:
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Run Command: `gunicorn civic.wsgi`
4. **Add PostgreSQL database**
5. **Set environment variables** (same as Railway)
6. **Deploy**

### Option 4: PythonAnywhere (Free tier available)

1. **Sign up** at [pythonanywhere.com](https://www.pythonanywhere.com)
2. **Upload your code** via Git or Files tab
3. **Create a Web App**
4. **Configure WSGI file** to point to `civic.wsgi`
5. **Set up database** (MySQL or PostgreSQL)
6. **Set environment variables** in Web App settings

## Pre-Deployment Checklist

### 1. Generate Secret Key
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Save this as your `SECRET_KEY` environment variable.

### 2. Update Database Settings
For production, use PostgreSQL instead of SQLite:
- Railway/Heroku: Automatically provides PostgreSQL
- Others: Create PostgreSQL database and update `DATABASES` in settings.py

### 3. Set Environment Variables
Create a `.env` file (don't commit it!) or set in your hosting platform:
```
SECRET_KEY=your-generated-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
```

### 4. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

## Post-Deployment Steps

1. **Import initial data**:
   ```bash
   python manage.py create_categories
   python manage.py import_corporators --csv gwmc_corporators_clean.csv
   ```

2. **Set up media storage**:
   - For production, configure cloud storage (AWS S3, Cloudinary)
   - Or use the hosting platform's storage solution

3. **Configure custom domain** (optional):
   - Point your domain to your hosting platform
   - Update `ALLOWED_HOSTS` to include your domain

4. **Set up SSL/HTTPS**:
   - Most platforms (Railway, Heroku) provide SSL automatically
   - For others, configure SSL certificate

## Troubleshooting

### Static files not loading?
- Run `python manage.py collectstatic`
- Check `STATIC_ROOT` and `STATIC_URL` settings
- Verify WhiteNoise is in `MIDDLEWARE`

### Database connection errors?
- Check database credentials in environment variables
- Verify database is running and accessible
- Check `ALLOWED_HOSTS` includes your domain

### 500 errors?
- Check logs in your hosting platform
- Verify `DEBUG=False` in production
- Check all environment variables are set

## Free Hosting Options Summary

| Platform | Free Tier | Database | SSL | Ease of Use |
|----------|-----------|----------|-----|-------------|
| Railway | ✅ Yes | ✅ PostgreSQL | ✅ Auto | ⭐⭐⭐⭐⭐ |
| Heroku | ⚠️ Limited | ✅ PostgreSQL | ✅ Auto | ⭐⭐⭐⭐ |
| PythonAnywhere | ✅ Yes | ✅ MySQL | ⚠️ Manual | ⭐⭐⭐ |
| Render | ✅ Yes | ✅ PostgreSQL | ✅ Auto | ⭐⭐⭐⭐ |
| Fly.io | ✅ Yes | ⚠️ Add-on | ✅ Auto | ⭐⭐⭐ |

## Recommended: Railway

Railway is the easiest option:
- Free tier with $5 credit/month
- Automatic PostgreSQL database
- Automatic SSL
- Simple Git-based deployment
- Great documentation

Visit: https://railway.app
