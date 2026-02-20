# 🚀 Quick Start - MeshWork Landing Page

## Start the Frontend

### Option 1: PowerShell (Recommended)
```powershell
cd frontend
npm install  # Only needed first time
npm run dev
```

Visit: **http://localhost:5173**

### Option 2: One-liner
```powershell
cd frontend; npm run dev
```

---

## What You'll See

### 1. Landing Page (Route: `/`)
- **Hero Section** with animated headline
- **Feature Grid** (3 pillars)
- **Gamification Teaser** with animated progress bar
- **Community Preview**
- **Final CTA**
- **Footer**

### 2. Auth Page (Route: `/auth`)
- Existing auth page (to be updated in Phase 2)

### 3. Dashboard (Route: `/dashboard`)
- Existing dashboard (requires login)

---

## Key Interactions to Test

### Navigation:
- Scroll down → Nav becomes solid with blur
- Click "Login" → Goes to `/auth`
- Click "Sign Up" → Goes to `/auth`

### Hero:
- Hover over "Get Started" button → Morphs to pill shape
- Watch floating UI preview → Slowly animates up/down

### Feature Cards:
- Hover over cards → Lift animation
- Scroll into view → Sequential fade-up

### Gamification Section:
- Scroll into view → Progress bar animates from 0 to 75%
- Watch for subtle glow after fill completes

### Buttons:
- All primary buttons morph to pill on hover
- All buttons have lift effect on hover
- Active state scales down slightly

---

## Test Scenarios

### Desktop (1920x1080):
```
✓ Full viewport hero
✓ Large typography (72px)
✓ 3-column feature grid
✓ Side-by-side gamification layout
✓ Wide navigation
```

### Tablet (768x1024):
```
✓ Responsive typography
✓ 2-column or stacked grids
✓ Proper spacing maintained
```

### Mobile (375x667):
```
✓ Single column layouts
✓ Scaled-down typography
✓ Readable text
✓ Touch-friendly buttons
✓ No horizontal scroll
```

---

## Design System Validation

### Colors Used:
- `#0E1113` - Background primary
- `#14181B` - Surface
- `#1B2024` - Surface elevated
- `#E6EDF3` - Text primary
- `#9AA4AE` - Text secondary
- `#10B981` - Accent emerald
- `#0EA371` - Accent hover

### Animations:
- Hero entrance: **150ms, 250ms, 350ms** stagger
- Scroll reveals: **500ms** duration
- Button morph: **300ms** transition
- Progress bar: **1.2s** fill

### Typography:
- Headlines: **72px** (desktop), **60px** (mobile)
- Section headings: **40px**
- Body: **18px**

---

## Expected First Impression

User lands → Thinks in **3 seconds**:

> **"This feels like a real product."**

Not:
- ❌ "This is a college project"
- ❌ "Another template site"
- ❌ "Too flashy/animated"

---

## Troubleshooting

### Port already in use:
```powershell
# Kill process on port 5173
netstat -ano | findstr :5173
taskkill /PID <pid_number> /F

# Or change port
npm run dev -- --port 3000
```

### Dependencies missing:
```powershell
cd frontend
rm -rf node_modules
rm package-lock.json
npm install
```

### Hot reload not working:
```powershell
# Restart dev server
# Press Ctrl+C to stop, then:
npm run dev
```

---

## Browser Testing

### Recommended Browsers:
- ✅ Chrome/Edge (Latest)
- ✅ Firefox (Latest)
- ✅ Safari (Latest)

### DevTools Testing:
1. Open DevTools (F12)
2. Go to "Network" tab
3. Reload page
4. Check: All assets load < 2s
5. Go to "Performance" tab
6. Record and check: 60fps animations

---

## Next Phase

Once landing page is reviewed and approved:

### Phase 2: Unified Auth Page
- Real-time email validation
- Dynamic form fields (student vs personnel)
- Design system compliance
- Backend integration

---

## Quick Links

- **Landing Page:** http://localhost:5173/
- **Auth Page:** http://localhost:5173/auth
- **Dashboard:** http://localhost:5173/dashboard
- **Backend API:** http://127.0.0.1:5000/

---

## Status

**Landing Page:** ✅ Complete
**Backend API:** ✅ Complete (Phase 1)
**Auth Page:** ⏳ Ready for Phase 2

---

**Ready to test!** 🚀
