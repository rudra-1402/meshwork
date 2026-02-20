# 🚀 Quick Start Guide - MeshWork v2.0

## Prerequisites
Before you begin, make sure you have:
- **Node.js 18+** installed ([Download](https://nodejs.org))
- **Python 3.9+** installed ([Download](https://python.org))
- **PostgreSQL** database running
- **Git** (optional, for cloning)

---

## 🎯 5-Minute Setup

### Step 1: Clone/Navigate to Project
```bash
cd F:\MeshWork
```

### Step 2: Install Frontend Dependencies
```bash
cd frontend
npm install
```

### Step 3: Install Backend Dependencies
```bash
cd ../backend

# Create virtual environment (if needed)
python -m venv venv

# Activate it
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install packages
pip install -r requirements.txt
```

### Step 4: Set Up Database
```bash
# Still in backend directory
flask db upgrade
```

### Step 5: Start Both Servers

**Terminal 1 - Backend**:
```bash
cd backend
venv\Scripts\activate
python run.py
```
✅ Backend running on http://localhost:5000

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```
✅ Frontend running on http://localhost:3000

---

## 🎨 What You'll See

1. **Landing Page** (http://localhost:3000):
   - Hero section with animated cards
   - Professional design with gradients
   - "Get Started" button leads to Auth

2. **Auth Page** (/auth):
   - Animated login/register toggle
   - Smooth field transitions
   - Beautiful form design

3. **Dashboard** (/dashboard):
   - Stats overview
   - Community sections
   - Leaderboard sidebar

---

## 🔧 Making Changes

### Frontend Changes
Edit files in `frontend/src/`:
- Pages in `pages/` folder
- Styles in `index.css`
- Components (create `components/` folder)

**Hot reload is automatic** - just save and see changes!

### Backend Changes
Edit files in `backend/app/`:
- Routes in `routes/` folder
- Models in `models/` folder
- Business logic in `services/` folder

Restart Flask server to see changes (or use `flask run --debug`).

---

## 📝 Common Commands

### Frontend
```bash
npm run dev       # Start dev server
npm run build     # Build for production
npm run preview   # Preview production build
npm run lint      # Check code quality
```

### Backend
```bash
python run.py              # Start server
flask db migrate -m "msg"  # Create migration
flask db upgrade           # Apply migrations
flask db downgrade         # Rollback migration
```

---

## 🎭 Testing the API

### Using curl
```bash
# Health check
curl http://localhost:5000/api/health

# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Test User\",\"email\":\"test@example.com\",\"password\":\"password123\"}"
```

### Using VS Code Thunder Client
1. Install Thunder Client extension
2. Create new request
3. Set URL: `http://localhost:5000/api/health`
4. Send!

---

## 🌙 Dark Mode

Currently, CSS variables are set up for dark mode. To toggle:

```javascript
// In browser console or add a button
document.documentElement.classList.toggle('dark')
```

**Next step**: Add a toggle button in the UI!

---

## 📦 Project Structure

```
MeshWork/
├── frontend/               # React app
│   ├── src/
│   │   ├── pages/         # Landing, Auth, Dashboard
│   │   ├── context/       # AuthContext
│   │   ├── utils/         # API config
│   │   └── index.css      # Design system
│   ├── package.json
│   └── vite.config.js
│
├── backend/               # Flask API
│   ├── app/
│   │   ├── routes/       # API endpoints
│   │   ├── models/       # Database models
│   │   └── services/     # Business logic
│   └── run.py
│
└── docs/                 # Documentation
```

---

## 🐛 Troubleshooting

### Frontend won't start
- Check Node.js version: `node --version` (should be 18+)
- Delete `node_modules` and run `npm install` again
- Check port 3000 is not in use

### Backend won't start
- Check Python version: `python --version` (should be 3.9+)
- Make sure virtual environment is activated
- Check PostgreSQL is running
- Verify database credentials in `backend/app/config.py`

### CORS errors
- Make sure backend is running on port 5000
- Check CORS configuration in `backend/app/__init__.py`
- Verify frontend proxy in `frontend/vite.config.js`

### Database errors
- Run migrations: `flask db upgrade`
- Check database connection string in config
- Ensure PostgreSQL service is running

---

## 🎓 Next Steps

### Immediate Tasks
1. ✅ Basic setup complete
2. 🔄 Connect Auth pages to real API
3. 🔄 Build component library
4. 🔄 Add error handling
5. 🔄 Implement dark mode toggle

### Learn More
- Read [ARCHITECTURE.md](./ARCHITECTURE.md) for full system overview
- Read [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md) for styling guide
- Check out existing routes in `backend/app/routes/`

---

## 💡 Tips

### Development Workflow
1. Start both servers (backend + frontend)
2. Make changes in VS Code
3. View changes in browser (auto-reload)
4. Check API responses in browser DevTools > Network
5. Debug with console.log / print statements

### Recommended VS Code Extensions
- **ES7+ React/Redux/React-Native snippets**
- **Tailwind CSS IntelliSense**
- **Thunder Client** (API testing)
- **Prettier** (code formatting)

### Browser DevTools
- **Console**: Check for JavaScript errors
- **Network**: Monitor API calls
- **React DevTools**: Inspect components
- **Application**: Check localStorage for JWT token

---

## 🆘 Need Help?

### Documentation
- [React Docs](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Flask Docs](https://flask.palletsprojects.com)
- [Framer Motion](https://www.framer.com/motion/)

### Common Issues
- **"Module not found"**: Run `npm install`
- **CORS error**: Check both servers are running
- **JWT error**: Clear localStorage and re-login
- **Database error**: Run migrations

---

## ✨ You're Ready!

Your development environment is now set up with:
✅ Modern React frontend with Vite
✅ Professional design system (Tailwind + custom tokens)
✅ Smooth animations (Framer Motion)
✅ Flask API backend with CORS
✅ JWT authentication ready
✅ Hot reload for both frontend and backend

**Start building! 🚀**

---

**Quick Start Version**: 1.0.0  
**Last Updated**: February 15, 2026
