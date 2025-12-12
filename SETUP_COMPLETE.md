# 🚀 Talentis.ai - Setup Complete!

## ✅ Both Servers Running

### Backend (FastAPI)
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Status**: ✅ Running with JWT authentication

### Frontend (React + Vite)
- **URL**: http://localhost:5173
- **Status**: ✅ Running with hot reload

---

## 🎯 Quick Start Guide

### 1. Auto-Login (Fastest Way)
Open http://localhost:5173 and click the **"Quick Login (Employer Demo)"** button.
- **Email**: employer@talentis.ai
- **Password**: password123
- **Role**: Employer

### 2. Manual Login Options

#### Employer Account (Pre-seeded)
- Email: `employer@talentis.ai`
- Password: `password123`
- Access: Employer Dashboard with job posting, match viewing, interview management

#### Candidate Accounts (Pre-seeded)
- Email: `candidate1@talentis.ai` or `candidate2@talentis.ai`
- Password: `password123`
- Access: Candidate Dashboard with interview list and results

### 3. Create New Account
Click "Register" tab and create a new account with any email/password.

---

## 🎨 Features Available

### Employer Dashboard (`/employer`)
- ✅ **Post New Jobs**: Title, description, skills, salary range, language
- ✅ **View Matches**: Auto-generated matches with AI scoring
- ✅ **Bias Audit**: See fairness metrics for each match (expandable panel)
- ✅ **Start AI Interview**: Launch AI-powered interviews for candidates
- ✅ **Analytics**: View time saved, CO2 reduced, retention predictions
- ✅ **Razorpay Integration**: Checkout when over free tier limit

### Candidate Dashboard (`/candidate`)
- ✅ **View Interviews**: See upcoming AI interviews
- ✅ **Join Interview**: Take 10 AI-generated questions based on job/skills
- ✅ **Submit Answers**: Text responses with real-time question tracking
- ✅ **View Results**: Technical, communication, cultural fit, retention scores
- ✅ **Upskilling Recommendations**: AI-generated learning paths

### Interview Modal (Both Roles)
- ✅ **10 Questions**: AI-generated based on job requirements and language
- ✅ **Answer Submission**: Text input with character count
- ✅ **Real-time Scoring**: Technical (40%), Communication (30%), Cultural Fit (30%)
- ✅ **Retention Prediction**: 1-5 years forecast
- ✅ **Recommendation**: Hire/Consider/Reject with explanation

---

## 🔐 API Endpoints (All Working)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/register` | Create new user account | ❌ |
| POST | `/api/login` | Login with email/password | ❌ |
| GET | `/api/me` | Get current user info | ✅ |
| POST | `/api/jobs` | Post new job (employer only) | ✅ |
| GET | `/api/jobs/{job_id}/matches` | Get matches for job | ✅ |
| POST | `/api/interview/start` | Start AI interview | ✅ |
| POST | `/api/interview/submit` | Submit interview answers | ✅ |
| POST | `/api/payments/create-order` | Create Razorpay order | ✅ |

**Authentication**: All protected endpoints require `Authorization: Bearer <JWT_TOKEN>` header.

---

## 🎭 Test Flow

### Complete Employer Flow:
1. Login as `employer@talentis.ai` / `password123`
2. Click "Post New Job"
3. Fill form: "Senior Python Developer", skills: "Python, FastAPI, PostgreSQL"
4. Submit → 2 matches auto-generated with bias audit scores
5. Click "Start AI Interview" for a match
6. Interview created, candidate can now join

### Complete Candidate Flow:
1. Login as `candidate1@talentis.ai` / `password123`
2. See "Upcoming Interviews" list
3. Click "Join Interview"
4. Answer 10 AI questions (supports English, Spanish, French, Hindi, Mandarin)
5. Submit → View Technical/Communication/Cultural scores
6. See retention prediction (e.g., "3 years") and recommendation
7. Get upskilling recommendations

---

## 🎨 Design Features

- **Purple/Teal Gradient**: Premium gradient background (`from-purple-900 via-purple-800 to-teal-700`)
- **Animated Background**: Glowing square canvas with hover effects
- **Framer Motion**: Butter-smooth page transitions and animations
- **React Hot Toast**: Beautiful notification system
- **Responsive**: Works on all screen sizes

---

## 🛠️ Tech Stack

### Backend
- FastAPI (Python web framework)
- SQLAlchemy 2.0 (ORM)
- SQLite (Database)
- JWT Authentication (python-jose)
- SHA256 Password Hashing
- CORS enabled for localhost:5173

### Frontend
- React 18
- Vite (Build tool)
- React Router v6 (Routing)
- Axios (HTTP client with JWT interceptor)
- Framer Motion (Animations)
- React Hot Toast (Notifications)
- TailwindCSS (Styling)

---

## 📊 Database Schema

**9 Tables**:
1. **Users** - Authentication and user profiles
2. **JobDescriptions** - Job postings with salary, skills, language
3. **Candidates** - Candidate profiles linked to users
4. **Matches** - AI-generated job-candidate matches with scores
5. **Interviews** - Interview sessions with questions/answers
6. **Payments** - Razorpay payment records
7. **Analytics** - Usage analytics for employers
8. **BiasAuditLogs** - Fairness audit trails
9. **SystemConfig** - System-wide configuration

---

## 🚦 Server Status Commands

### Check Both Servers
```bash
lsof -i :8000 -i :5173 | grep LISTEN
```

### Restart Backend
```bash
cd /workspaces/talentis.ai/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Restart Frontend
```bash
cd /workspaces/talentis.ai/frontend
npm run dev
```

---

## 🎉 Ready to Use!

**Open in browser**: http://localhost:5173

Click "Quick Login (Employer Demo)" to start exploring immediately!

---

## 📝 Notes

- **Auto-seeding**: Database auto-seeds with 1 employer, 2 candidates, 1 job, 2 matches on first run
- **JWT Expiry**: Tokens expire after 30 days
- **Free Tier**: First 10 interviews/month free, then Razorpay checkout required
- **Languages Supported**: English, Spanish, French, Hindi, Mandarin for interviews
- **Bias Audit**: Every match includes fairness metrics (gender, ethnicity, age scoring)

---

## 🐛 Troubleshooting

**Backend not responding?**
```bash
cd /workspaces/talentis.ai/backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend not responding?**
```bash
cd /workspaces/talentis.ai/frontend && npm run dev
```

**Login not working?**
- Check backend is running at http://localhost:8000
- Check browser console for errors
- Try auto-login button first
- Verify CORS is allowing localhost:5173

**"uvicorn: command not found"?**
```bash
cd /workspaces/talentis.ai/backend && pip install -r requirements.txt
```

---

**Built with ❤️ using FastAPI, React, and AI**
