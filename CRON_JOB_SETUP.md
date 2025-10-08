# Daily Recommendations Cron Job Setup

## Overview
This cron job pre-generates order recommendations daily at 3 AM, ensuring instant response when users access the system during business hours.

## Backend Endpoint
```
POST /api/v1/recommended-order/pre-generate-daily?date=YYYY-MM-DD&route_code=1004
```

## Cron Schedule

### For Linux/Unix Servers

**Option 1: Using crontab**
```bash
# Edit crontab
crontab -e

# Add this line to run at 3 AM daily (generates for next day)
0 3 * * * /usr/bin/curl -X POST "https://your-api-domain.com/api/v1/recommended-order/pre-generate-daily?date=$(date -d '+1 day' +\%Y-\%m-\%d)&route_code=1004" >> /var/log/yaumi_cron.log 2>&1
```

**Option 2: Using Python script**
```bash
# Save this as /opt/yaumi/cron_generate_recommendations.py
import requests
from datetime import datetime, timedelta

# Calculate tomorrow's date
tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

# API endpoint
url = f"https://your-api-domain.com/api/v1/recommended-order/pre-generate-daily"
params = {
    "date": tomorrow,
    "route_code": "1004"
}

# Make request
response = requests.post(url, params=params)
print(f"{datetime.now()}: {response.json()}")

# Crontab entry:
# 0 3 * * * /usr/bin/python3 /opt/yaumi/cron_generate_recommendations.py >> /var/log/yaumi_cron.log 2>&1
```

### For Windows Servers

**Using Task Scheduler**
1. Open Task Scheduler
2. Create Basic Task → Name: "Yaumi Daily Recommendations"
3. Trigger: Daily at 3:00 AM
4. Action: Start a program
   - Program: `curl.exe`
   - Arguments: `-X POST "https://your-api-domain.com/api/v1/recommended-order/pre-generate-daily?date=$(powershell -Command "(Get-Date).AddDays(1).ToString('yyyy-MM-dd')")&route_code=1004"`

**PowerShell Script (Recommended)**
```powershell
# Save as C:\Scripts\Generate-Recommendations.ps1
$tomorrow = (Get-Date).AddDays(1).ToString("yyyy-MM-dd")
$url = "https://your-api-domain.com/api/v1/recommended-order/pre-generate-daily?date=$tomorrow&route_code=1004"

try {
    $response = Invoke-RestMethod -Uri $url -Method Post
    Write-Output "$(Get-Date): $($response | ConvertTo-Json)"
} catch {
    Write-Error "$(Get-Date): Failed - $_"
}

# Task Scheduler Action:
# powershell.exe -ExecutionPolicy Bypass -File "C:\Scripts\Generate-Recommendations.ps1"
```

### For Cloud Platforms (Render, Heroku, etc.)

**Render.com - Using Cron Jobs**
1. Add to `render.yaml`:
```yaml
services:
  - type: cron
    name: yaumi-daily-recommendations
    env: production
    schedule: "0 3 * * *"  # 3 AM daily
    buildCommand: echo "Cron job"
    startCommand: curl -X POST "https://yaumi-api.onrender.com/api/v1/recommended-order/pre-generate-daily?date=$(date -d '+1 day' +\%Y-\%m-\%d)&route_code=1004"
```

**Heroku - Using Heroku Scheduler**
```bash
# Install scheduler addon
heroku addons:create scheduler:standard

# Add job via Heroku Dashboard or CLI
heroku addons:open scheduler

# Job command (Daily at 3 AM):
curl -X POST "$API_URL/api/v1/recommended-order/pre-generate-daily?date=$(date -u -d '+1 day' +\%Y-\%m-\%d)&route_code=1004"
```

## Timezone Considerations

**Production servers in different timezones:**

- **UAE/Saudi Arabia (UTC+4)**: Run at 23:00 UTC (previous day)
  ```bash
  0 23 * * * curl ...
  ```

- **Pakistan/India (UTC+5)**: Run at 22:00 UTC (previous day)
  ```bash
  0 22 * * * curl ...
  ```

- **Server in UTC**: Run at 3 AM local target timezone
  ```bash
  # For UAE (UTC+4), run at 23:00 UTC previous day = 3 AM UAE time next day
  0 23 * * * curl ...
  ```

## Monitoring & Logging

**View logs:**
```bash
# Linux
tail -f /var/log/yaumi_cron.log

# View last 50 lines
tail -n 50 /var/log/yaumi_cron.log
```

**Success response:**
```json
{
  "success": true,
  "message": "Successfully generated and saved recommendations for 2024-10-08",
  "action": "generated",
  "date": "2024-10-08",
  "route_code": "1004",
  "records_saved": 1547,
  "generation_time_seconds": 42.3,
  "generated_at": "2024-10-07T23:00:15.234Z"
}
```

**If already exists:**
```json
{
  "success": true,
  "message": "Recommendations already exist for 2024-10-08",
  "action": "skipped",
  "date": "2024-10-08",
  "existing_records": 1547
}
```

## Testing the Cron Job

**Manual test (run now):**
```bash
# Replace with your API URL
curl -X POST "https://your-api-domain.com/api/v1/recommended-order/pre-generate-daily?date=2024-10-08&route_code=1004"
```

**Expected behavior:**
1. First run: Generates recommendations (~30-60s) → Returns `"action": "generated"`
2. Second run: Skips (already exists) → Returns `"action": "skipped"`

## Troubleshooting

**Issue: Cron job not running**
```bash
# Check crontab is active
service cron status

# Check cron logs
grep CRON /var/log/syslog

# Verify user has permissions
ls -la /var/log/yaumi_cron.log
```

**Issue: API timeout**
- Increase timeout in curl: `curl -m 300 ...` (5 minutes)
- Check backend is running
- Verify database connection

**Issue: Invalid date format**
```bash
# Test date command
date -d '+1 day' +%Y-%m-%d

# If fails, use alternative:
date -v+1d +%Y-%m-%d  # macOS/BSD
```

## Multiple Routes Support

To generate for multiple routes daily:
```bash
# Generate for routes 1004, 1005, 1006
0 3 * * * for route in 1004 1005 1006; do curl -X POST "https://your-api-domain.com/api/v1/recommended-order/pre-generate-daily?date=$(date -d '+1 day' +\%Y-\%m-\%d)&route_code=$route"; sleep 5; done >> /var/log/yaumi_cron.log 2>&1
```

Or use Python script:
```python
import requests
from datetime import datetime, timedelta

tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
routes = ['1004', '1005', '1006']

for route in routes:
    url = f"https://your-api-domain.com/api/v1/recommended-order/pre-generate-daily"
    params = {"date": tomorrow, "route_code": route}
    response = requests.post(url, params=params)
    print(f"{datetime.now()} Route {route}: {response.json()}")
```

## Best Practices

1. **Always log cron output** to track successes/failures
2. **Use absolute paths** in cron commands
3. **Set email notifications** for cron failures (if supported)
4. **Monitor execution time** to ensure job completes before business hours
5. **Test manually first** before automating
6. **Keep timezone consistent** between server and business hours
