# GitHub Setup Instructions

## Step 1: Create GitHub Repository

1. Go to [github.com](https://github.com)
2. Click **"New repository"** (green button)
3. Repository settings:
   - **Name**: `Yaumi_Live`
   - **Description**: `Production-ready Yaumi Analytics Platform - FMCG Sales Analytics & Supervision`
   - **Visibility**: **Private** (recommended for production code)
   - **DO NOT** initialize with README (we already have one)
   - **DO NOT** add .gitignore (we already have one)
   - **DO NOT** add license yet
4. Click **"Create repository"**

## Step 2: Push Local Code to GitHub

GitHub will show you commands. Use these:

```bash
cd C:/Users/divya/Desktop/Yaumi/Yaumi_Live

# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/Yaumi_Live.git

# Rename branch to main (if needed)
git branch -M main

# Push code
git push -u origin main
```

## Step 3: Verify Security

After pushing, check:

1. **No .env files in repo**:
   - Go to GitHub repo
   - Search for ".env" (should only find .env.example)

2. **No credentials visible**:
   - Check `backend/config/settings.py`
   - Should only see `os.getenv()` calls
   - No hardcoded passwords/IPs

3. **Protected files in .gitignore**:
   - View `.gitignore` file
   - Verify all sensitive patterns listed

## Step 4: Configure Branch Protection (Optional)

For team projects:

1. Go to **Settings** -> **Branches**
2. Click **"Add rule"**
3. Branch name pattern: `main`
4. Enable:
   - Require pull request reviews before merging
   - Require status checks to pass
   - Include administrators

## Step 5: Add Collaborators (Optional)

1. Go to **Settings** -> **Collaborators**
2. Click **"Add people"**
3. Enter GitHub username/email
4. Set permissions (Write/Maintain/Admin)

## Security Reminders

- Repository is PRIVATE
- No .env files committed
- No credentials in code
- .gitignore protects sensitive files
- All secrets in .env.example are placeholders

## Next Steps

After pushing to GitHub:

1. **Deploy Backend**: Follow `DEPLOYMENT.md` -> Step 1
2. **Deploy Frontend**: Follow `DEPLOYMENT.md` -> Step 2
3. **Configure Monitoring**: Set up UptimeRobot
4. **Team Notification**: Share deployment URLs

---

## Troubleshooting

**Q: Git says "remote already exists"**
```bash
# Remove old remote and add new one
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/Yaumi_Live.git
```

**Q: Permission denied (publickey)**
```bash
# Use HTTPS instead
git remote set-url origin https://github.com/YOUR_USERNAME/Yaumi_Live.git
```

**Q: I see .env in GitHub**
```bash
# Remove it immediately
git rm --cached backend/.env
git commit -m "Remove .env file"
git push origin main

# Then change your database password
```

---

**Your code is ready to push**
