import {
  CalendarDays,
  ClipboardList,
  FolderGit2,
  Home,
  Trophy,
  User,
  Users,
  ShieldCheck,
  GraduationCap,
} from 'lucide-react'

export const STUDENT_NAV_ITEMS = [
  { label: 'Home', href: '/home', icon: Home },
  { label: 'Profile', href: '/profile', icon: User },
  { label: 'Questionnaire', href: '/questionnaire', icon: ClipboardList },
  { label: 'Leaderboard', href: '/leaderboard', icon: Trophy },
  { label: 'Projects', href: '/projects', icon: FolderGit2 },
  { label: 'Events', href: '/events', icon: CalendarDays },
  { label: 'Communities', href: '/communities/explore', icon: Users },
]

export const STUDENT_TOP_ITEMS = [
  { label: 'Home', href: '/home', icon: Home },
  { label: 'Profile', href: '/profile', icon: User },
  { label: 'Questionnaire', href: '/questionnaire', icon: ClipboardList },
  { label: 'Leaderboard', href: '/leaderboard', icon: Trophy },
]

export const PERSONNEL_NAV_ITEMS = [
  { label: 'Home', href: '/personnel/dashboard', icon: Home },
  { label: 'Students', href: '/personnel/students', icon: GraduationCap },
  { label: 'Whitelist', href: '/personnel/whitelist', icon: ShieldCheck },
]
