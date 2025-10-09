# Sales Supervision - Production Deployment Checklist

## ✅ Pre-Deployment Verification

### Code Changes Verification
- [ ] All frontend changes in `SalesSupervision.tsx` deployed
- [ ] All backend changes in `sales_supervision.py` deployed
- [ ] All backend changes in `supervision_storage.py` deployed
- [ ] All backend changes in `dynamic_supervisor.py` deployed
- [ ] No syntax errors in modified files
- [ ] TypeScript compilation successful
- [ ] Python linting passed

### Testing Verification
- [ ] Unit tests passed
- [ ] Integration tests passed
- [ ] Manual testing completed
- [ ] Staging environment testing completed

### Documentation Verification
- [ ] `PRODUCTION_FIXES_SUMMARY.md` reviewed
- [ ] Team briefed on changes
- [ ] Rollback plan documented

---

## 🚀 Phase 1 Deployment (Immediate)

### Step 1: Backup
- [ ] Database backup completed
- [ ] Code backup/tag created

### Step 2: Frontend Deployment
```bash
# Build frontend
cd frontend
npm run build

# Deploy to production
# ... your deployment command ...
```

- [ ] Frontend build successful
- [ ] Frontend deployed
- [ ] Frontend health check passed

### Step 3: Backend Deployment
```bash
# Install dependencies (if any new ones)
pip install -r requirements.txt

# Restart backend server
# ... your restart command ...
```

- [ ] Backend dependencies installed
- [ ] Backend restarted
- [ ] Backend health check passed

### Step 4: Smoke Testing
- [ ] Open Sales Supervision page
- [ ] Select route and date
- [ ] Toggle visited customer
- [ ] Edit actual quantity
- [ ] Generate customer analysis
- [ ] Generate route analysis
- [ ] Save session
- [ ] Reload page and verify historical mode works

### Step 5: Monitoring
- [ ] Check error logs (0 errors expected)
- [ ] Monitor API response times
- [ ] Monitor LLM cache hit rate
- [ ] Check database performance

---

## ⚠️ Phase 2 Deployment (Optional - Optimistic Locking)

**Schedule:** Within 1-2 weeks after Phase 1

### Step 1: Schedule Maintenance Window
- [ ] Maintenance window scheduled
- [ ] Users notified
- [ ] Backup completed

### Step 2: Run Database Migration
```sql
-- Run this script in SQL Server Management Studio
-- File: backend/database/migrations/add_optimistic_locking.sql

USE YaumiAIML;
GO

ALTER TABLE [dbo].[tbl_supervision_route_summary]
ADD record_version INT NOT NULL DEFAULT 1;
GO

CREATE INDEX idx_route_session_version
ON [dbo].[tbl_supervision_route_summary](session_id, record_version);
GO
```

- [ ] Migration script executed
- [ ] Column added successfully
- [ ] Index created successfully

### Step 3: Deploy Backend Updates
- [ ] Update `supervision_storage.py` with version checks
- [ ] Deploy backend
- [ ] Restart server

### Step 4: Deploy Frontend Updates
- [ ] Update error handling for version conflicts
- [ ] Deploy frontend

### Step 5: Test Concurrent Users
- [ ] Open session in two browsers
- [ ] User A makes changes and saves
- [ ] User B makes different changes and saves
- [ ] Verify User B gets version conflict error

---

## 🧪 Quick Smoke Tests

### Test 1: Basic Flow (2 min)
```
1. Select route 1004, date today
2. Click visited toggle on customer
3. Edit actual quantity to 10
4. Click "Save Session"
Expected: Success message appears
```

### Test 2: Historical Mode (1 min)
```
1. Reload page
2. Select same route and date
Expected: Blue "Read-Only" badge appears
Expected: Cannot edit quantities
Expected: Cannot toggle visited
```

### Test 3: LLM Analysis (1 min)
```
1. Click "Customer Review" button
2. Wait for analysis
Expected: Analysis appears in <1s (cached) or <5s (new)
3. Click again
Expected: Instant response (from cache)
```

### Test 4: Rate Limiting (30 sec)
```
1. Click "Customer Review" rapidly 3 times
Expected: Error message after first click
Expected: Countdown timer showing wait time
```

### Test 5: Validation (30 sec)
```
1. Edit quantity to -5
Expected: Resets to 0
2. Edit quantity to 1000000
Expected: Error: "Quantity cannot exceed 999,999"
```

---

## 🚨 Rollback Plan

### If Critical Issues Detected

#### Rollback Frontend
```bash
# Revert to previous version
git checkout <previous-commit>
npm run build
# Deploy previous build
```

#### Rollback Backend
```bash
# Revert to previous version
git checkout <previous-commit>
# Restart server
```

#### Rollback Database (Phase 2 only)
```sql
-- Remove optimistic locking column
ALTER TABLE [YaumiAIML].[dbo].[tbl_supervision_route_summary]
DROP COLUMN record_version;

DROP INDEX idx_route_session_version
ON [YaumiAIML].[dbo].[tbl_supervision_route_summary];
```

---

## 📊 Success Metrics

### Immediate (Day 1)
- [ ] Zero production errors related to supervision
- [ ] LLM cache hit rate > 50%
- [ ] Average save time < 2 seconds
- [ ] No duplicate session IDs

### Week 1
- [ ] LLM cache hit rate > 70%
- [ ] LLM cost reduction visible in bills
- [ ] No data integrity issues reported
- [ ] User feedback positive

### Week 4
- [ ] LLM cache hit rate > 85%
- [ ] Monthly LLM cost reduced by $100-200
- [ ] Zero concurrent user conflicts
- [ ] Performance improved by 2x

---

## 📞 Emergency Contacts

- **Backend Issues:** Check backend logs
- **Frontend Issues:** Check browser console
- **Database Issues:** Check SQL Server logs
- **LLM Issues:** Check Groq API dashboard

---

## ✅ Sign-Off

- [ ] Development Lead reviewed
- [ ] QA Lead approved
- [ ] DevOps ready
- [ ] Product Owner informed

**Deployment Date:** _______________
**Deployed By:** _______________
**Issues Encountered:** _______________

---

**Last Updated:** 2025-01-10
