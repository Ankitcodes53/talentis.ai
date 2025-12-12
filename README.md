# Talentis.ai 🚀

> AI-powered global hiring platform connecting exceptional talent with amazing opportunities worldwide.

![Talentis.ai](https://img.shields.io/badge/AI-Hiring%20Platform-8b5cf6?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TailwindCSS](https://img.shields.io/badge/Tailwind-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

## ✨ Features

- 🤖 **AI-Powered Matching**: Advanced algorithms match candidates with perfect job opportunities
- 🌍 **Global Reach**: Connect with talent and opportunities from around the world
- ⚡ **Real-time Updates**: Stay informed with instant notifications
- 📊 **Smart Analytics**: Data-driven insights for better hiring decisions
- 🎨 **Modern UI**: Unique design with dynamic animated background and butter-smooth transitions
- 📱 **Responsive**: Works seamlessly on all devices

## 🏗️ Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **Python 3.11+**: Core programming language
- **SQLite**: Lightweight database for data persistence
- **Pydantic**: Data validation using Python type annotations
- **LangChain**: AI/LLM integration framework
- **Uvicorn**: ASGI server implementation

### Frontend
- **React 18**: UI library for building interactive interfaces
- **Vite**: Next-generation frontend tooling
- **React Router**: Client-side routing
- **Framer Motion**: Smooth animations and transitions
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: Promise-based HTTP client

### Database
- **SQLite**: Embedded relational database (development)
- **PostgreSQL**: Production-ready database (migration ready)
- **SQLAlchemy 2.0**: Modern Python ORM
- **Alembic**: Database migration tool
- Schema includes: Users, JobDescriptions, Candidates, Matches, Interviews, Payments, Analytics, BiasAuditLogs

## 📁 Project Structure

```
talentis.ai/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main API application
│   ├── requirements.txt    # Python dependencies
│   └── __init__.py
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   │   ├── AnimatedBackground.jsx
│   │   │   ├── AnimatedBackground.css
│   │   │   └── Navbar.jsx
│   │   ├── pages/         # Page components
│   │   │   ├── Home.jsx
│   │   │   ├── Jobs.jsx
│   │   │   ├── Candidates.jsx
│   │   │   └── About.jsx
│   │   ├── App.jsx        # Root component
│   │   ├── main.jsx       # Entry point
│   │   └── index.css      # Global styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
├── db/                    # Database files
│   ├── schema.sql        # SQLite schema with full definitions
│   ├── schema_postgresql.sql  # PostgreSQL-optimized schema
│   ├── migrate_db.py     # SQLAlchemy migration script
│   ├── SCHEMA_DOCUMENTATION.md  # Complete schema docs
│   ├── QUICK_REFERENCE.md  # Quick reference guide
│   ├── init.sql          # Legacy schema (reference)
│   └── README.md
├── .gitignore
├── vercel.json           # Vercel deployment config
├── netlify.toml          # Netlify deployment config
├── setup.sh              # Setup script
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/talentis.ai.git
cd talentis.ai

# Make setup script executable
chmod +x setup.sh

# Run setup script
./setup.sh
```

### Option 2: Manual Setup

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Database Setup

```bash
# Navigate to db directory
cd db

# Initialize database with SQLAlchemy models
python migrate_db.py --create-tables --seed-data

# Or just create tables without sample data
python migrate_db.py --create-tables

# View database information
python migrate_db.py --info

cd ..
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## 💻 Development

### Running the Backend

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`

### Running the Frontend

```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:3000`

### Running Both Simultaneously

**Terminal 1** (Backend):
```bash
cd backend && source venv/bin/activate && uvicorn main:app --reload
```

**Terminal 2** (Frontend):
```bash
cd frontend && npm run dev
```

## 🎨 Design Features

### Animated Background
- Dynamic canvas with subtle square boxes
- Glow effect on hover with smooth animations
- Responsive to mouse movements
- Optimized performance with RequestAnimationFrame

### Color Palette
- Base gradient: `#f0f4f8` to `#e2e8f0` (soft blue-gray)
- Accent purple: `#8b5cf6`
- Accent blue: `#3b82f6`
- Accent teal: `#14b8a6`

### Animations
- Framer Motion for page transitions
- Smooth hover effects with scale transforms
- Gradient animations on CTAs
- Fade-in effects for content

## 📡 API Endpoints

### Authentication & Users
- `POST /api/users` - Create new user account
- `GET /api/users/{user_id}` - Get user profile

### Jobs
- `GET /api/jobs` - Get all jobs (with pagination & filters)
- `GET /api/jobs/{job_id}` - Get specific job
- `POST /api/jobs` - Create new job posting (requires employer_id)

### Candidates
- `POST /api/candidates` - Register new candidate (requires user_id)
- `GET /api/candidates/{candidate_id}` - Get candidate profile

### AI Matching
- `POST /api/ai/match` - Generate AI matches for a job
- `GET /api/matches/job/{job_id}` - Get all matches for a job

### Analytics
- `GET /api/analytics/user/{user_id}` - Get user analytics and ROI metrics

### Bias Auditing
- `GET /api/bias-audit/flagged` - Get bias audits flagged for review

### Health
- `GET /health` - Health check endpoint
- `GET /` - API information

## 🗄️ Database Schema

### Core Tables

1. **users** - User accounts for employers and candidates
   - Roles: employer, candidate, admin
   - Authentication fields and activity tracking

2. **job_descriptions** - Job postings with AI-ready structure
   - JSON skills array for flexible matching
   - Location, salary, experience requirements

3. **candidates** - Comprehensive candidate profiles
   - Resume text and URL storage
   - JSON skills, languages, education
   - Social profile links

4. **matches** - AI-powered job-candidate matching
   - Match score (0-100) with detailed explanation
   - Skills matching breakdown
   - Status tracking (pending, accepted, rejected)

5. **interviews** - Interview management system
   - AI-generated questions (JSON)
   - Video recording URLs
   - Multi-dimensional scoring (technical, communication, cultural fit)

6. **payments** - Payment and subscription management
   - Multiple plans: freemium, pay-per-hire, monthly, annual
   - Transaction tracking with external gateway integration

7. **analytics** - ROI tracking and user metrics
   - Flexible JSON storage for various metrics
   - Retention, engagement, conversion data

8. **bias_audit_logs** - AI transparency and fairness
   - Bias detection metrics
   - Fairness scoring
   - Mitigation strategy logging

For detailed schema documentation, see:
- `db/SCHEMA_DOCUMENTATION.md` - Complete ERD and table specs
- `db/QUICK_REFERENCE.md` - Quick reference guide
- `db/schema.sql` - SQLite schema
- `db/schema_postgresql.sql` - PostgreSQL schema

## 🌐 Deployment

### Deploying to Vercel (Recommended for Full-Stack)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel
```

The `vercel.json` configuration handles both frontend and backend deployment.

### Deploying to Netlify (Frontend Only)

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy
```

For backend, consider using:
- **Railway**: Easy Python deployment
- **Render**: Free tier available
- **Fly.io**: Global edge deployment

### Environment Variables

Create `.env` files for production:

**Backend** (`.env`):
```
DATABASE_URL=sqlite:///./db/talentis.db
OPENAI_API_KEY=your_openai_key_here
CORS_ORIGINS=https://your-frontend-url.com
```

**Frontend** (`.env`):
```
VITE_API_URL=https://your-backend-url.com
```

## 🧪 Testing

```bash
# Backend tests (TODO: Add pytest)
cd backend
pytest

# Frontend tests (TODO: Add vitest)
cd frontend
npm test
```

## 📝 Future Enhancements

- [ ] User authentication (JWT)
- [ ] Advanced AI matching with LangChain
- [ ] Real-time chat between recruiters and candidates
- [ ] Video interview scheduling
- [ ] Resume parsing with AI
- [ ] Advanced analytics dashboard
- [ ] Email notifications
- [ ] Social media integration
- [ ] Mobile app (React Native)
- [ ] Multi-language support

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent backend framework
- React team for the amazing UI library
- Tailwind CSS for the utility-first CSS framework
- Framer Motion for smooth animations
- LangChain for AI integration capabilities

## 📞 Contact

For questions or feedback, please open an issue or reach out to the development team.

---

**Built with ❤️ using AI-powered technologies**