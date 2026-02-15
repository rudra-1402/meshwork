# MeshWork Frontend

Modern React SPA built with Vite, Tailwind CSS, and Framer Motion.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🛠️ Tech Stack

- **React 18**: Component-based UI
- **Vite**: Fast build tool
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Smooth animations
- **Lucide React**: Beautiful icons
- **React Router**: SPA routing
- **Axios**: HTTP client

## 📁 Structure

```
src/
├── pages/          # Page components
├── context/        # React Context providers
├── utils/          # Utilities (API client)
└── index.css       # Global styles + design system
```

## 🎨 Design System

See [../DESIGN_SYSTEM.md](../DESIGN_SYSTEM.md) for:
- Color palette
- Typography
- Components
- Dark mode

## 🔌 API Configuration

Environment variables in `.env`:
```env
VITE_API_URL=http://localhost:5000/api
```

API client auto-adds JWT token from localStorage.

## 📖 Documentation

- [Architecture](../ARCHITECTURE.md)
- [Design System](../DESIGN_SYSTEM.md)
- [Quick Start](../QUICK_START.md)
- [Migration Guide](../MIGRATION_GUIDE.md)

## 🌙 Dark Mode

Toggle dark mode:
```javascript
document.documentElement.classList.toggle('dark')
```

## 🐛 Troubleshooting

**Port already in use:**
```bash
# Kill process on port 3000 (Windows)
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**CORS errors:**
- Ensure backend is running on localhost:5000
- Check proxy configuration in `vite.config.js`

## 📝 Scripts

- `npm run dev` - Start dev server
- `npm run build` - Production build
- `npm run preview` - Preview build locally
- `npm run lint` - Check code quality
