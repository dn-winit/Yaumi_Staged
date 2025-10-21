# Recommendation Database Setup & Cron Job Configuration

## 🎯 **Overview**

This system pre-generates daily recommendations at night and stores them in YaumiAIML database for **instant user access** (< 1 second response time).

**Before:** First request = 125 seconds, subsequent = instant
**After:** ALL requests = instant (< 1 second) ✅

---

## 📋 **Setup Steps**

### **Step 1: Create Database Table**

Run this SQL script **ONCE** in YaumiAIML database:

```sql
-- File: backend/sql/create_recommended_orders_table.sql
-- Connect to YaumiAIML database and execute
```

**What it creates:**
- Table: `[YaumiAIML].[dbo].[tbl_recommended_orders]`
- Indexes for fast queries
- Unique constraint to prevent duplicates

**Verify table creation:**
```sql
SELECT TOP 10 * FROM [YaumiAIML].[dbo].[tbl_recommended_orders];
```

---

### **Step 2: Test Pre-Generation Endpoint**

Test manually before setting up cron:

```bash
# Generate recommendations for tomorrow
curl -X POST "https://staged.onrender.com/api/v1/recommended-order/pre-generate-daily?date=2025-10-08"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Successfully generated and saved recommendations for 2025-10-08",
  "action": "generated",
  "date": "2025-10-08",
  "route_code": "1004",
  "records_saved": 189,
  "generation_time_seconds": 125.5,
  "generated_at": "2025-10-07T09:30:15.123456"
}
```

**Verify in database:**
```sql
SELECT COUNT(*) as total, COUNT(DISTINCT customer_code) as customers
FROM [YaumiAIML].[dbo].[tbl_recommended_orders]
WHERE trx_date = '2025-10-08';
```

---

### **Step 3: Set Up Cron Job**

## **Option A: Using cron-job.org (Recommended for Simplicity)**

1. **Go to:** https://cron-job.org
2. **Create Account** (free)
3. **Create New Cron Job:**
   - **Title:** Daily Yaumi Recommendations
   - **Address:** `https://staged.onrender.com/api/v1/recommended-order/pre-generate-daily`
   - **Schedule:** Every day at **3:00 AM** (your local time)
   - **Request Method:** POST
   - **Query Parameters:**
     - Key: `date`
     - Value: Use **dynamic date** (set to "tomorrow" using cron-job.org's variables)
   - **Timezone:** Asia/Dubai (or your timezone)

4. **Save and Enable**

---

## **Option B: Using Render Cron Jobs**

**Note:** Render requires a separate cron job service (paid feature)

If you have Render cron jobs enabled:

1. **Create** `render.yaml` in project root:

```yaml
services:
  - type: web
    name: staged-backend
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port 10000

  - type: cron
    name: daily-recommendations
    env: python
    schedule: "0 23 * * *"  # 11 PM UTC = 3 AM UAE (UTC+4)
    buildCommand: pip install -r backend/requirements.txt
    startCommand: |
      TOMORROW=$(date -d "tomorrow" +%Y-%m-%d)
      curl -X POST "https://staged.onrender.com/api/v1/recommended-order/pre-generate-daily?date=$TOMORROW"
```

2. **Commit and push** `render.yaml`
3. Render will auto-detect and create the cron job

---

## **Best Time for Middle East / Asia**

**Recommended:** **3:00 AM Local Time** (before business hours)

| Region | Timezone | Local Time | UTC Time |
|--------|----------|------------|----------|
| **UAE/Saudi Arabia** | UTC+4 | 3:00 AM | 11:00 PM (previous day) |
| **Pakistan** | UTC+5 | 3:00 AM | 10:00 PM (previous day) |
| **India** | UTC+5:30 | 3:00 AM | 9:30 PM (previous day) |
| **Bangladesh** | UTC+6 | 3:00 AM | 9:00 PM (previous day) |

**Why 3 AM?**
- ✅ No users online
- ✅ Database has updated with previous day's actuals
- ✅ Recommendations ready before business hours (8-9 AM)
- ✅ No interference with daytime operations

---

## **How It Works**

### **Night (3 AM) - Cron Job Runs:**
```
1. Cron triggers API call with tomorrow's date
2. System generates recommendations (125 seconds)
3. Saves ~190 records to YaumiAIML database
4. Done - no one waiting!
```

### **Day (Business Hours) - User Requests:**
```
1. User opens Recommended Order page
2. Frontend calls /get-recommendations-data
3. Backend fetches from database (< 1 second)
4. User sees instant results! 🎉
```

---

## **API Endpoints**

### **1. Pre-Generate (for Cron)**
```http
POST /api/v1/recommended-order/pre-generate-daily?date=YYYY-MM-DD
```

**When to use:** Cron job only
**What it does:** Generates and saves to database
**Response time:** ~125 seconds (no one waiting)

---

### **2. Get Recommendations (for Users)**
```http
POST /api/v1/recommended-order/get-recommendations-data
Body: { "date": "YYYY-MM-DD", ... filters ... }
```

**When to use:** User requests from frontend
**What it does:** Fetches from database (fast), generates if missing (fallback)
**Response time:**
- From database: **< 1 second** ✅
- Generated on-demand: ~125 seconds (only if cron failed)

---

## **Monitoring & Maintenance**

### **Check if Cron is Running:**

```sql
-- Latest generation
SELECT TOP 10
    trx_date,
    COUNT(*) as records,
    generated_at,
    generated_by
FROM [YaumiAIML].[dbo].[tbl_recommended_orders]
GROUP BY trx_date, generated_at, generated_by
ORDER BY generated_at DESC;
```

### **Check Today's Recommendations:**

```sql
SELECT COUNT(*) as total_recommendations
FROM [YaumiAIML].[dbo].[tbl_recommended_orders]
WHERE trx_date = CAST(GETDATE() AS DATE);
```

### **View Generation History:**

```sql
SELECT
    trx_date as date,
    COUNT(*) as recommendations,
    MIN(generated_at) as generated_at,
    generated_by
FROM [YaumiAIML].[dbo].[tbl_recommended_orders]
GROUP BY trx_date, generated_by
ORDER BY trx_date DESC;
```

---

## **Troubleshooting**

### **Problem: Cron job failed**

**Symptoms:**
- No recommendations in database for today
- Users see "generating..." and wait 125 seconds

**Solution:**
1. **Check cron-job.org logs** (if using external service)
2. **Manually trigger** pre-generation:
   ```bash
   curl -X POST "https://staged.onrender.com/api/v1/recommended-order/pre-generate-daily?date=2025-10-08"
   ```
3. **Check Render logs** for errors

---

### **Problem: Recommendations missing for specific date**

**Solution:**
```bash
# Regenerate for specific date
curl -X POST "https://staged.onrender.com/api/v1/recommended-order/pre-generate-daily?date=2025-10-08"
```

---

### **Problem: Old data accumulating**

**Solution: Clean up old recommendations** (optional - keep 90 days)

```sql
-- Delete recommendations older than 90 days
DELETE FROM [YaumiAIML].[dbo].[tbl_recommended_orders]
WHERE trx_date < DATEADD(day, -90, GETDATE());
```

**Recommended:** Run this monthly or set up auto-cleanup

---

## **Benefits Summary**

✅ **Always Instant** - Users never wait (< 1 second)
✅ **Reliable** - Database more robust than CSV files
✅ **Scalable** - Handles concurrent users
✅ **History** - Can query past recommendations
✅ **Professional** - Industry-standard approach
✅ **Cost-effective** - Free cron services available

---

## **Next Steps**

1. ✅ **Create table** in YaumiAIML (run SQL script once)
2. ✅ **Test endpoint** manually
3. ✅ **Set up cron job** (cron-job.org or Render)
4. ✅ **Monitor** for first few days
5. ✅ **Enjoy instant responses!** 🚀

---

## **Support**

If issues arise:
1. Check database table exists
2. Verify cron job is enabled
3. Check Render logs for errors
4. Test endpoint manually
5. Verify database credentials are correct

**All set! Your recommendations will now generate nightly and users get instant responses!** 🎉
