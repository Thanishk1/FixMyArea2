# How to Push to GitHub

## Step 1: Create a GitHub Repository

1. Go to https://github.com and sign in (or create an account)
2. Click the **"+"** icon in the top right → **"New repository"**
3. Fill in:
   - **Repository name**: `fixmyarea` (or any name you like)
   - **Description**: "Civic Issues Portal - Report and track civic issues"
   - **Visibility**: Choose Public or Private
   - **DO NOT** check "Initialize with README" (we already have files)
4. Click **"Create repository"**

## Step 2: Copy Your Repository URL

After creating the repository, GitHub will show you a URL like:
- `https://github.com/yourusername/fixmyarea.git`

Copy this URL - you'll need it in the next step!

## Step 3: Connect and Push

Run these commands in your terminal (replace with YOUR repository URL):

```bash
git remote add origin https://github.com/yourusername/fixmyarea.git
git branch -M main
git push -u origin main
```

## Alternative: If you already have a GitHub repo

If you already created a repository, just run:

```bash
git remote add origin https://github.com/yourusername/your-repo-name.git
git branch -M main
git push -u origin main
```

## Authentication

When you push, GitHub will ask for authentication:
- **Option 1**: Use GitHub Personal Access Token (recommended)
  - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  - Generate new token with `repo` permissions
  - Use this token as your password when pushing

- **Option 2**: Use GitHub CLI (`gh auth login`)

## Troubleshooting

### If you get "remote origin already exists":
```bash
git remote remove origin
git remote add origin https://github.com/yourusername/fixmyarea.git
```

### If you get authentication errors:
- Make sure you're using a Personal Access Token, not your password
- Or use GitHub Desktop app for easier authentication

## Success!

Once pushed, your code will be on GitHub and you can:
- Deploy to Railway/Render/Heroku
- Share with others
- Track changes with version control
