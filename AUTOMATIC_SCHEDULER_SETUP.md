# Automatic Scheduler - Complete Setup

## ✅ What's Implemented

The system now has **built-in automatic scheduling** that runs inside the FastAPI application. No external cron job setup needed!

---

## 🎯 How It Works

### **1. Automatic Startup**

When you start the backend:
```bash
cd backend
python main.py
```

The scheduler **automatically starts** and runs in the background.

**Console Output:**
```
============================================================
YAUMI ANALYTICS API - STARTING UP
Environment: development
API Version: 2.0.0
============================================================
Starting background data loading thread...
Starting automatic scheduler for daily recommendations...
[SCHEDULER] ✓ Started - Will run daily at 03:00
[SCHEDULER] Next run: 2024-10-09 03:00:00
============================================================
YAUMI ANALYTICS API - READY
Data is loading in background thread...
Scheduler is running - Daily recommendations at 3 AM
============================================================
```

### **2. Daily Execution at 3 AM**

Every day at 3 AM (server local time), the scheduler:

1. **Calculates tomorrow's date**
2. **Generates recommendations** for all configured routes
3. **Saves to database** (`tbl_recommended_orders`)
4. **Logs the results**

**Log Output (at 3 AM):**
```
[CRON] Starting daily recommendation generation for 2024-10-09
[CRON] Generating for route 1004...
[CRON] ✓ Route 1004: Successfully generated and saved recommendations for 2024-10-09
[CRON] Completed daily generation for 2024-10-09
```

### **3. User Access (9 AM Business Hours)**

When users access the system:

**Recommended Order Page:**
```
User selects date: 2024-10-09
    ↓
Auto-fetch from DB
    ↓
✓ Instant load (<1 second) - Data already generated at 3 AM!
```

**Sales Supervision Page:**
```
User selects route 1004 + date 2024-10-09 → Apply Filters
    ↓
Backend checks DB
    ↓
✓ Instant load - Data already exists!
    ↓
Auto-fills: Customers to Visit + Recommended Order sections
```

---

## ⚙️ Configuration

### **Environment Variables (.env)**

```bash
# Optional - Customize scheduler behavior
CRON_HOUR=3           # Hour to run (24-hour format, default: 3)
CRON_MINUTE=0         # Minute to run (default: 0)
CRON_ROUTES=1004      # Routes to generate (comma-separated)

# Examples:
CRON_HOUR=3           # 3 AM
CRON_MINUTE=30        # 3:30 AM
CRON_ROUTES=1004,1005,1006  # Multiple routes
```

**If not set, defaults:**
- Time: 3:00 AM server local time
- Routes: 1004

---

## 📊 Monitor Scheduler Status

### **Check Scheduler Status**

```bash
# API endpoint
GET /api/v1/scheduler/status
```

**Response:**
```json
{
  "running": true,
  "jobs": [
    {
      "id": "daily_recommendations",
      "name": "Generate Daily Recommendations",
      "next_run": "2024-10-09 03:00:00",
      "trigger": "cron[hour='3', minute='0']"
    }
  ],
  "message": "1 job(s) scheduled"
}
```

### **View Logs**

```bash
# Backend logs
tail -f backend/logs/yaumi_analytics.log

# Filter for scheduler logs
tail -f backend/logs/yaumi_analytics.log | grep "\[CRON\]\|\[SCHEDULER\]"
```

---

## 🔄 Complete Data Flow

### **Day 1 - Initial Setup**

```
8:00 AM - You start the backend
    ↓
Scheduler starts automatically
    ↓
Next run scheduled: Tomorrow at 3:00 AM
```

### **Day 2 - First Automatic Generation**

```
3:00 AM - Scheduler triggers automatically
    ↓
Generates recommendations for 2024-10-09 (tomorrow)
    ↓
Saves to database (route 1004)
    ↓
Scheduler reschedules: Next run at 3:00 AM Day 3
```

```
9:00 AM - User accesses Recommended Order page
    ↓
Selects date: 2024-10-09
    ↓
Backend: Checks DB → ✓ Found (generated at 3 AM)
    ↓
Returns instantly (<1 second)
```

```
9:30 AM - User accesses Sales Supervision
    ↓
Selects route 1004 + date 2024-10-09 → Apply Filters
    ↓
Backend: Checks DB → ✓ Found
    ↓
Auto-fills Customers to Visit + Recommended Orders
```

### **Day 3+ - Ongoing**

```
3:00 AM Daily - Auto-generates tomorrow's recommendations
9:00 AM Daily - Users get instant access to pre-generated data
```

---

## 🛠️ Installation

### **1. Install Dependencies**

```bash
pip install -r backend/requirements.txt
```

This installs `apscheduler>=3.10.0` (added to requirements.txt)

### **2. Start Backend**

```bash
cd backend
python main.py
```

**That's it!** Scheduler starts automatically.

---

## 🔧 Troubleshooting

### **Issue: Scheduler Not Running**

**Check logs:**
```bash
tail -f backend/logs/yaumi_analytics.log | grep SCHEDULER
```

**Expected output:**
```
[SCHEDULER] ✓ Started - Will run daily at 03:00
```

**If not appearing:**
1. Ensure `apscheduler` is installed: `pip install apscheduler`
2. Restart backend: `python main.py`

### **Issue: Scheduler Running But No Data Generated**

**Check cron logs:**
```bash
tail -f backend/logs/yaumi_analytics.log | grep CRON
```

**Manual test:**
```bash
# Trigger generation manually
curl -X POST "http://localhost:8000/api/v1/recommended-order/pre-generate-daily?date=2024-10-09&route_code=1004"
```

**Verify database:**
```sql
SELECT COUNT(*) FROM tbl_recommended_orders WHERE trx_date = '2024-10-09';
```

### **Issue: Wrong Timezone**

**Check server timezone:**
```bash
# Linux
timedatectl

# Windows
tzutil /g
```

**Adjust in .env:**
```bash
# If server is in UTC but you want 3 AM local time (e.g., UAE UTC+4)
# Set to run at 23:00 UTC (11 PM) = 3 AM local time next day
CRON_HOUR=23  # For UTC+4 timezone
```

---

## 🆚 Comparison: Manual vs Automatic

### **Before (Manual OS Cron)**

```bash
# Setup required on every server
crontab -e
0 3 * * * curl -X POST "http://localhost:8000/api/v1/..."

# Issues:
❌ Manual setup on each deployment
❌ Different syntax per OS (Linux/Windows)
❌ No visibility in app logs
❌ Harder to debug
```

### **After (Automatic In-App Scheduler)**

```bash
# Just start the app
python main.py

# Benefits:
✅ Zero manual setup
✅ Works on all platforms (Linux/Windows/Mac)
✅ Integrated with app logs
✅ Easy to monitor and debug
✅ Configured via .env file
```

---

## 📝 Best Practices

1. **Monitor Logs Daily**
   ```bash
   grep "\[CRON\]" backend/logs/yaumi_analytics.log
   ```

2. **Set Up Email Alerts (Optional)**
   - Configure email notifications for failed generations
   - Monitor database record counts

3. **Test Before Production**
   ```bash
   # Change time to run in 2 minutes
   CRON_HOUR=$(date +%H)
   CRON_MINUTE=$(($(date +%M) + 2))

   # Start backend and verify it runs
   python main.py
   ```

4. **Multiple Routes Configuration**
   ```bash
   # In .env
   CRON_ROUTES=1004,1005,1006
   ```

---

## 🚀 Deployment

### **Development**
```bash
python main.py
# Scheduler starts automatically
```

### **Production (Render, Heroku, etc.)**

**No changes needed!** Scheduler runs automatically when app starts.

**render.yaml:**
```yaml
services:
  - type: web
    name: yaumi-api
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: python backend/main.py
    # Scheduler starts automatically - no cron job needed!
```

---

## ✅ Summary

**What You Get:**

1. ✅ **Automatic scheduler** runs at 3 AM daily
2. ✅ **Zero manual setup** - just start the app
3. ✅ **Pre-generates recommendations** for all routes
4. ✅ **Saves to database** for instant access
5. ✅ **Users get instant load** during business hours
6. ✅ **Cross-platform** - works everywhere
7. ✅ **Easy monitoring** via logs and status endpoint

**What Users Experience:**

- **Recommended Order Page:** Instant load (<1s) after date selection
- **Sales Supervision:** Auto-fills customers + recommendations on Apply Filters
- **No waiting time** during business hours
- **Always up-to-date** data

**Perfect!** 🎯
