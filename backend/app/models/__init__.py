"""Models package — export every model so `from app.models import X` always works."""

# Core user / college
from app.models.user import User
from app.models.college import College
from app.models.college_personnel import CollegePersonnel
from app.models.whitelisted_email import WhitelistedEmail

# Projects
from app.models.project import Project, ProjectStatus, MembershipPolicy, ProjectVisibility
from app.models.project_member import ProjectMember, ProjectMemberRole
from app.models.project_language import ProjectLanguage
from app.models.language import Language
from app.models.user_language import UserLanguage

# Scoring
from app.models.scoring import UserScoring
from app.models.scoring_history import ScoringHistory

# Gamification
from app.models.user_skill import UserSkill
from app.models.xp_transaction import XPTransaction

# Community
from app.models.community import Community
from app.models.community_member import CommunityMember
from app.models.community_moderator import CommunityModerator
from app.models.community_task import CommunityTask
from app.models.task_completion import TaskCompletion
from app.models.community_message import CommunityMessage
from app.models.community_poll import CommunityPoll, PollVote
from app.models.community_file import CommunityFile

# Events
from app.models.event_models import Event, EventParticipant, EventTask, EventTaskCompletion