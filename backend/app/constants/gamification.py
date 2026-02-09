"""
Gamification System Constants

All XP amounts, limits, formulas, and rules in ONE centralized location.
Modify values here to tune the entire gamification system.
"""

# ===== XP SYSTEM =====

# Daily XP cap (anti-farming)
DAILY_XP_CAP = 300

# XP amounts for each action
XP_AMOUNTS = {
    # Login & Streaks
    'daily_login': 10,
    'streak_bonus_7': 25,
    'streak_bonus_30': 150,
    'streak_bonus_90': 500,
    'streak_bonus_150': 1000,
    
    # Challenges
    'challenge_complete': 100,
    'challenge_perfect_score': 50,  # Bonus for 100% correct
    
    # Tasks (smaller work items)
    'task_complete': 25,
    
    # Projects
    'project_submit': 150,
    'project_featured': 100,  # Admin features it
    
    # Events
    'event_rsvp': 5,
    'event_attended': 50,
    'event_organized': 200,
    
    # Community
    'community_join': 20,
    'helpful_comment': 5,  # When upvoted by others
    
    # Admin adjustments
    'admin_bonus': 0,  # Variable amount set by admin
    'admin_penalty': 0,  # Variable amount set by admin
}


# ===== DIMINISHING RETURNS =====

# Maximum number of FULL XP awards per action type per day
ACTION_DAILY_LIMITS = {
    'challenge': 3,      # After 3 challenges, XP reduced
    'task': 10,          # After 10 tasks, XP reduced
    'project': 2,        # After 2 projects, XP reduced
    'helpful_comment': 5,  # After 5 helpful comments, XP reduced
}

# Diminishing returns multipliers
# After hitting daily limit:
# - Next N actions: 50% XP
# - After that: 10% XP (minimum)
DIMINISHING_RETURNS_STAGES = [
    (1.0, "Full XP"),      # Below limit
    (0.5, "50% XP"),       # 1-2x limit
    (0.1, "10% XP"),       # 2x+ limit
]


# ===== LEVEL FORMULA =====

# Standard formula: level = floor(sqrt(xp / LEVEL_DIVISOR)) + 1
LEVEL_FORMULA_DIVISOR = 100

# Level thresholds (for reference and testing)
# Generated from: xp = LEVEL_DIVISOR × (level - 1)²
LEVEL_THRESHOLDS = [
    (0, 1),          # 0-99 XP → Level 1
    (100, 2),        # 100-399 XP → Level 2
    (400, 3),        # 400-899 XP → Level 3
    (900, 4),        # 900-1599 XP → Level 4
    (1600, 5),       # 1600-2499 XP → Level 5
    (2500, 6),       # 2500-3599 XP → Level 6
    (3600, 7),       # 3600-4899 XP → Level 7
    (4900, 8),       # 4900-6399 XP → Level 8
    (6400, 9),       # 6400-8099 XP → Level 9
    (8100, 10),      # 8100-9999 XP → Level 10
    (10000, 11),     # 10000-12099 XP → Level 11
    (12100, 12),     # 12100-14399 XP → Level 12
    (14400, 13),     # 14400-16899 XP → Level 13
    (16900, 14),     # 16900-19599 XP → Level 14
    (19600, 15),     # 19600-22499 XP → Level 15
    (22500, 16),     # 22500-25599 XP → Level 16
    (25600, 17),     # 25600+ XP → Level 17+
    # Add more as needed up to Level 50
]


# ===== STREAK SYSTEM =====

# Streak milestone bonuses (day count → bonus XP)
STREAK_BONUS_XP = {
    7: 25,       # 1 week
    30: 150,     # 1 month
    90: 500,     # 3 months
    150: 1000,   # 5 months
}


# ===== REPUTATION SYSTEM =====

# Vote weights for reputation changes
REPUTATION_WEIGHTS = {
    # Project votes
    'project_upvote': +2,
    'project_downvote': -1,
    
    # Challenge votes
    'challenge_upvote': +3,
    'challenge_downvote': -1,
    
    # Comment votes
    'comment_upvote': +1,
    'comment_downvote': -1,
    
    # Moderation
    'content_flagged_spam': -5,
    'content_flagged_plagiarism': -10,
    'content_restored': +5,
}

# Reputation cannot go below this value
REPUTATION_FLOOR = None  # None = can go negative


# ===== SKILL SYSTEM =====

# Skill weight validation
MIN_DOMINANT_SKILL_WEIGHT = 30  # At least one skill must be ≥30%
SKILL_WEIGHT_SUM_TOLERANCE = 1  # Allow ±1% tolerance (99-101%)

# Available skills (can be expanded)
AVAILABLE_SKILLS = [
    # Programming Languages
    'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust',
    'PHP', 'Ruby', 'Swift', 'Kotlin', 'R', 'MATLAB', 'Scala',
    
    # Web Technologies
    'HTML', 'CSS', 'React', 'Vue', 'Angular', 'Node.js', 'Express',
    'Django', 'Flask', 'FastAPI', 'Spring Boot', 'ASP.NET',
    
    # Databases
    'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
    
    # DevOps & Tools
    'Docker', 'Kubernetes', 'Git', 'CI/CD', 'AWS', 'Azure', 'GCP',
    
    # Data & ML
    'Machine Learning', 'Deep Learning', 'Data Analysis', 'TensorFlow',
    'PyTorch', 'Pandas', 'NumPy',
    
    # Mobile
    'iOS Development', 'Android Development', 'React Native', 'Flutter',
    
    # Other
    'UI/UX Design', 'System Design', 'Algorithms', 'Testing', 'Security',
]


# ===== FLAIR SYSTEM (Phase 2) =====

# Flair definitions will be added when achievement system is implemented
FLAIR_REQUIREMENTS = {
    # Streak-based flairs
    'streak_15': {'type': 'streak', 'days': 15, 'icon': '🔥', 'name': 'On Fire'},
    'streak_30': {'type': 'streak', 'days': 30, 'icon': '🔥🔥', 'name': 'Burning Hot'},
    'streak_90': {'type': 'streak', 'days': 90, 'icon': '🔥🔥🔥', 'name': 'Unstoppable'},
    'streak_150': {'type': 'streak', 'days': 150, 'icon': '👑🔥', 'name': 'Streak Legend'},
    
    # Challenge-based flairs
    'challenge_5': {'type': 'challenge', 'count': 5, 'icon': '🧩', 'name': 'Problem Solver'},
    'challenge_15': {'type': 'challenge', 'count': 15, 'icon': '🧩🧩', 'name': 'Challenge Master'},
    'challenge_50': {'type': 'challenge', 'count': 50, 'icon': '🧩🧩🧩', 'name': 'Challenge Legend'},
    
    # Level-based flairs
    'level_5': {'type': 'level', 'level': 5, 'icon': '📚', 'name': 'Scholar'},
    'level_10': {'type': 'level', 'level': 10, 'icon': '📚📚', 'name': 'Expert'},
    'level_25': {'type': 'level', 'level': 25, 'icon': '📚📚📚', 'name': 'Master'},
    'level_50': {'type': 'level', 'level': 50, 'icon': '👑📚', 'name': 'Grandmaster'},
}


# ===== VALIDATION RULES =====

# XP transaction limits
MIN_XP_TRANSACTION = -1000  # Maximum penalty in single transaction
MAX_XP_TRANSACTION = 500    # Maximum bonus in single transaction (except admin)

# Skill XP limits
MIN_SKILL_XP_AWARD = 1
MAX_SKILL_XP_AWARD = 200

# Username display limits
MAX_USERNAME_LENGTH = 150

# Description limits
MAX_DESCRIPTION_LENGTH = 500