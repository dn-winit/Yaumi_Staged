# Deployment Guide - Render + Vercel

## Pre-Deployment Checklist

- [ ] All sensitive data removed from code
- [ ] `.env.example` updated with all required variables
- [ ] `.gitignore` configured properly
- [ ] Code pushed to GitHub (main branch)
- [ ] Database accessible from internet (or configure VPN/allowlist)
- [ ] Region: Asia Pacific (Singapore) - for optimal performance in your region

---

## Step 1: Deploy Backend to Render.com

### 1.1 Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Verify email

### 1.2 Deploy from GitHub

1. Click **"New +"** -> **"Web Service"**
2. Connect GitHub repository: `Yaumi_Live`
3. Configure deployment settings:
   - **Region**: Select **Singapore** (Asia Pacific region for best performance)
   - Render auto-detects `render.yaml` configuration
4. Click **"Apply"**

### 1.3 Configure Environment Variables

Go to **Dashboard** -> **yaumi-backend** -> **Environment**

Add these secret variables:

```bash
# Database (REQUIRED)
DB_SERVER=your-server-ip
DB_NAME=YaumiAIML
DB_USER=your-username
DB_PASSWORD=your-secure-password

# Analytics Engine (REQUIRED)
GROQ_API_KEY=your-analytics-api-key

# Security (REQUIRED)
SECRET_KEY=generate-using-python-secrets

# CORS (Update after frontend deployment)
CORS_ORIGINS=https://*.vercel.app,https://yaumi-frontend.vercel.app
```

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 1.4 Deploy & Monitor

1. Click **"Manual Deploy"** -> **"Deploy latest commit"**
2. Monitor logs in Dashboard
3. Wait for "Build successful" message
4. Note your backend URL: `https://yaumi-backend.onrender.com`

### 1.5 Test Backend

```bash
curl https://yaumi-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-..."
}
```

---

## Step 2: Deploy Frontend to Vercel

### 2.1 Create Vercel Account
1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Verify email

### 2.2 Deploy from GitHub

#### Option A: Dashboard (Easiest)

1. Click **"Add New"** -> **"Project"**
2. Import GitHub repo: `Yaumi_Live`
3. Configure project:
   - **Framework Preset**: Vite
   - **Root Directory**: `./`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Region**: Automatically optimized for Asia Pacific (Singapore edge network)

4. **Environment Variables**:
   ```bash
   VITE_API_URL=https://yaumi-backend.onrender.com/api/v1
   ```

5. Click **"Deploy"**

**Note for Asia Pacific**: Vercel automatically serves your app from the nearest edge location (Singapore) for optimal performance in the region.

#### Option B: CLI (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd /path/to/Yaumi_Live
vercel

# Set environment variable
vercel env add VITE_API_URL production
# Enter: https://yaumi-backend.onrender.com/api/v1

# Deploy to production
vercel --prod
```

### 2.3 Get Frontend URL

You'll receive: `https://yaumi-frontend.vercel.app`

---

## Step 3: Update CORS Configuration

### 3.1 Update Backend CORS

Go to **Render Dashboard** -> **yaumi-backend** -> **Environment**

Update `CORS_ORIGINS`:
```bash
CORS_ORIGINS=https://yaumi-frontend.vercel.app,https://yaumi-frontend-git-*.vercel.app
```

Click **"Save Changes"** - Backend auto-redeploys

### 3.2 Test Connection

1. Open `https://yaumi-frontend.vercel.app`
2. Check browser console for errors
3. Test API calls (Dashboard, Forecast, etc.)

---

## Step 4: Keep Backend Awake (Optional)

Render free tier sleeps after 15 minutes of inactivity.

### Option 1: UptimeRobot (Free)

1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Sign up (free)
3. Add New Monitor:
   - **Type**: HTTP(s)
   - **URL**: `https://yaumi-backend.onrender.com/health`
   - **Monitoring Interval**: 5 minutes
4. Save

**Result**: Backend stays awake 24/7

### Option 2: GitHub Actions

Create `.github/workflows/keep-alive.yml`:

```yaml
name: Keep Backend Alive

on:
  schedule:
    - cron: '*/14 * * * *'  # Every 14 minutes

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping backend
        run: curl https://yaumi-backend.onrender.com/health
```

---

## Step 5: Monitoring & Logs

### Render Logs (Backend)
- Dashboard -> yaumi-backend -> **Logs**
- Real-time log streaming
- Filter by severity (INFO, ERROR, etc.)

### Vercel Logs (Frontend)
- Dashboard -> yaumi-frontend -> **Deployments** -> Click deployment -> **Logs**
- Build logs and runtime logs

---

## Continuous Deployment

Both platforms auto-deploy on git push:

```bash
git add .
git commit -m "Update feature"
git push origin main

# Automatically triggers:
# - Render: Backend rebuild & deploy
# - Vercel: Frontend rebuild & deploy
```

---

## Troubleshooting

### Backend Issues

**Problem**: Database connection fails
```
Solution:
1. Check DB_SERVER, DB_USER, DB_PASSWORD in Render env vars
2. Ensure SQL Server allows connections from Render IP
3. Check SQL Server firewall settings
```

**Problem**: Analytics API key not working
```
Solution:
1. Verify key in Render Dashboard -> Environment
2. Check service console for usage/limits
3. Ensure key has correct permissions
```

**Problem**: CORS errors in browser
```
Solution:
1. Update CORS_ORIGINS in Render to include your Vercel domain
2. Redeploy backend after env var change
3. Clear browser cache
```

### Frontend Issues

**Problem**: API calls fail (404, 500)
```
Solution:
1. Verify VITE_API_URL in Vercel env vars
2. Check backend is running (visit /health endpoint)
3. Check browser console for exact error
```

**Problem**: Blank page after deployment
```
Solution:
1. Check Vercel build logs for errors
2. Verify dist/ folder generated correctly
3. Check vercel.json rewrites configuration
```

---

## Security Post-Deployment

### Immediate Actions:

1. **Change Database Password**
   ```bash
   # Ensure strong password is set
   # Update DB_PASSWORD in Render env vars
   ```

2. **Review Access Logs**
   - Check SQL Server logs for unauthorized access
   - Review Render deployment logs

3. **Enable 2FA**
   - Enable on GitHub account
   - Enable on Render account
   - Enable on Vercel account

4. **Monitor API Usage**
   - Check analytics service dashboard for unusual activity
   - Set up usage alerts if available

---

## Performance Optimization

### Backend (Render)

**Region**: Singapore (Asia Pacific)
- Free tier: Cold starts after 15min inactivity
- **Upgrade from Free Tier** (when needed):
  - Starter Plan: $7/month (faster, no sleep)
  - Always-on, 512MB RAM
  - Singapore region ensures low latency for Asia Pacific users

### Frontend (Vercel)

**Edge Network**: Automatically optimized for Asia Pacific
- Served from Singapore edge nodes
- Sub-100ms latency across Asia Pacific region
- Automatic edge caching
- Image optimization available
- Global CDN with Asia Pacific priority routing

---

## Custom Domain (Optional)

### For Backend (Render):
1. Dashboard -> yaumi-backend -> **Settings** -> **Custom Domains**
2. Add: `api.yaumi.com`
3. Update DNS records at domain registrar

### For Frontend (Vercel):
1. Dashboard -> yaumi-frontend -> **Settings** -> **Domains**
2. Add: `app.yaumi.com`
3. Update DNS records at domain registrar

---

## Support

### Render Support
- Docs: https://render.com/docs
- Community: https://community.render.com

### Vercel Support
- Docs: https://vercel.com/docs
- Discord: https://vercel.com/discord

---

## Deployment Complete

Your application is now live:

- **Frontend**: https://yaumi-frontend.vercel.app
- **Backend**: https://yaumi-backend.onrender.com
- **API Docs** (dev only): https://yaumi-backend.onrender.com/api/docs

**Next Steps:**
1. Share URLs with team
2. Test all features thoroughly
3. Monitor logs for errors
4. Set up analytics (optional)
5. Configure custom domains (optional)
