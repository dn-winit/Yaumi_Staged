# 🎯 WINIT Analytics Platform

**Professional Sales Intelligence & Forecasting System**

Version 2.0.0 | Production Ready

---

## 📋 Overview

Enterprise-grade analytics platform for sales demand forecasting, intelligent recommendations, and real-time supervision.

### **Core Modules:**
- 🎯 **Demand Forecasting** - AI-powered demand prediction
- 🛍️ **Recommended Orders** - Tiered recommendation engine
- 👁️ **Sales Supervision** - Real-time route monitoring with LLM analysis
- 📊 **Analytics Dashboard** - Performance insights and KPIs

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- SQL Server (YaumiAIML database access)
- Groq API key (for LLM features)

### Installation

```bash
# 1. Install backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Install frontend
npm install

# 3. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 4. Run backend
python -m backend.main

# 5. Run frontend (new terminal)
npm run dev
```

**Access:** http://localhost:5173

---

## 📚 Documentation

- **[Complete Documentation](./docs/README.md)** - All guides and references
- **[Deployment Guide](./docs/deployment/DEPLOYMENT_CHECKLIST.md)** - Production deployment
- **[Database Setup](./docs/setup/RECOMMENDATION_DATABASE_SETUP.md)** - Database configuration

---

## 🏗️ Architecture

```
Yaumi_Live/
├── backend/           # FastAPI backend
│   ├── core/         # Business logic
│   ├── routes/       # API endpoints
│   ├── database/     # DB connections & migrations
│   ├── models/       # Data models
│   └── prompts/      # LLM templates
├── src/              # React frontend
│   ├── components/   # UI components
│   ├── services/     # API clients
│   └── types/        # TypeScript types
└── docs/             # Documentation
```

---

## 🔒 Security

- Environment-based configuration
- SQL injection prevention
- Input validation & rate limiting
- Transaction integrity

See **[SECURITY.md](./docs/SECURITY.md)** for details.

---

## 📝 Version History

### v2.0.0 (2025-01-10)
- ✅ Sales Supervision production fixes
- ✅ LLM caching & rate limiting
- ✅ Transaction rollback protection
- ✅ Historical mode implementation

---

**Built for Professional Sales Intelligence** 🚀