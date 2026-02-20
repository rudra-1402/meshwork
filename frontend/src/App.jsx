import { Routes, Route, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { AuthProvider } from './context/AuthContext'
import Landing from './pages/Landing'
import Auth from './pages/Auth'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import Questionnaire from './pages/Questionnaire'
import Leaderboard from './pages/Leaderboard'
import Projects from './pages/Projects'
import ProjectsNew from './pages/ProjectsNew'
import ProjectDetail from './pages/ProjectDetail'
import Events from './pages/Events'
import EventDetail from './pages/EventDetail'
import CommunitiesExplore from './pages/CommunitiesExplore'
import CommunityDetail from './pages/CommunityDetail'
import PersonnelDashboard from './pages/PersonnelDashboard'
import NotFound from './pages/NotFound'
import CollegeRegisterPage from './pages/CollegeRegisterPage'
import AdminLoginPage from './pages/AdminLoginPage'

function App() {
  return (
    <AuthProvider>
      <AnimatePresence mode="wait">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/auth" element={<Auth />} />
          <Route path="/home" element={<Home />} />
          <Route path="/college/register" element={<CollegeRegisterPage token="" />} />
          <Route path="/college/admin-login" element={<AdminLoginPage token="" />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/questionnaire" element={<Questionnaire />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/personnel/dashboard" element={<PersonnelDashboard />} />
          <Route path="/projects/new" element={<ProjectsNew />} />
          <Route path="/projects/:projectId" element={<ProjectDetail />} />
          <Route path="/events" element={<Events />} />
          <Route path="/events/:eventId" element={<EventDetail />} />
          <Route path="/communities/explore" element={<CommunitiesExplore />} />
          <Route path="/communities/:communityId" element={<CommunityDetail />} />
          <Route path="/student/home" element={<Navigate to="/home" replace />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AnimatePresence>
    </AuthProvider>
  )
}

export default App
