"""
Project Service

All business logic for project lifecycle, membership, and discovery.
Routes must not contain any logic from this file.

Dependency direction: project_service -> language_proficiency_service
                      project_service -> xp_service
                      project_service -> models
"""

import logging
from datetime import datetime, timezone

from app.extensions import db
from app.models.project import Project, ProjectStatus, MembershipPolicy, ProjectVisibility
from app.models.project_member import ProjectMember, ProjectMemberRole
from app.models.project_language import ProjectLanguage
from app.models.language import Language
from app.models.user import User
from app.services.language_proficiency_service import LanguageProficiencyService
from app.services.xp_service import XPService
from app.constants.gamification import XP_AMOUNTS

logger = logging.getLogger(__name__)

# =============================================================================
# STATE MACHINE — Single source of truth for valid project transitions.
# Any transition not listed here is BLOCKED.
# =============================================================================
VALID_TRANSITIONS = {
    ProjectStatus.DRAFT:       [ProjectStatus.OPEN],
    ProjectStatus.OPEN:        [ProjectStatus.IN_PROGRESS, ProjectStatus.CANCELLED],
    ProjectStatus.IN_PROGRESS: [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED],
    ProjectStatus.COMPLETED:   [],
    ProjectStatus.CANCELLED:   [],
}

# Instantiate dependent services
_lang_service = LanguageProficiencyService()


class ProjectService:
    """
    Service layer for all project-related operations.

    Handles creation, forking, updates, membership management,
    language XP awards, and discovery ranking.
    """

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    @staticmethod
    def _resolve_language_names(language_ids):
        """
        Resolve a list of language IDs to their name strings.
        Required because LanguageProficiencyService accepts names, not IDs.

        Args:
            language_ids: List of integer language IDs

        Returns:
            List of language name strings. Silently skips unknown IDs.
        """
        if not language_ids:
            return []
        languages = Language.query.filter(Language.id.in_(language_ids)).all()
        return [lang.name for lang in languages]

    @staticmethod
    def _get_project_or_none(project_id):
        """Fetch project by ID. Returns None if not found."""
        return db.session.get(Project, project_id)

    @staticmethod
    def _get_member_or_none(project_id, user_id):
        """Fetch membership record. Returns None if not found."""
        return ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()

    @staticmethod
    def _is_owner(project_id, user_id):
        """Check if user is an OWNER of this project."""
        member = ProjectService._get_member_or_none(project_id, user_id)
        return member is not None and member.role == ProjectMemberRole.OWNER

    @staticmethod
    def _owner_count(project_id):
        """Return count of current owners for a project."""
        return ProjectMember.query.filter_by(
            project_id=project_id,
            role=ProjectMemberRole.OWNER
        ).count()

    # =========================================================================
    # CREATE PROJECT
    # =========================================================================

    @staticmethod
    def create_project(creator_id, data):
        """
        Create a new project. Atomically creates project record,
        inserts creator as owner, and attaches languages.

        Args:
            creator_id: Integer — authenticated user's ID
            data: Dict with keys:
                  - title (required, str)
                  - description (optional, str)
                  - status (optional, ProjectStatus — defaults to DRAFT)
                  - membership_policy (optional, MembershipPolicy — defaults to REQUEST)
                  - visibility (optional, ProjectVisibility — defaults to PRIVATE)
                  - interest_tags (optional, list of str)
                  - language_ids (optional, list of int)

        Returns:
            tuple: (success: bool, message: str, project: Project or None)
        """
        title = data.get('title', '').strip()
        if not title:
            return False, "Project title is required", None

        if len(title) > 200:
            return False, "Project title must be 200 characters or fewer", None

        try:
            project = Project(
                title=title,
                description=data.get('description'),
                creator_id=creator_id,
                status=data.get('status', ProjectStatus.DRAFT),
                membership_policy=data.get('membership_policy', MembershipPolicy.REQUEST),
                visibility=data.get('visibility', ProjectVisibility.PRIVATE),
                interest_tags=data.get('interest_tags') or [],
            )
            db.session.add(project)
            db.session.flush()  # Obtain project.id before related inserts

            # Insert creator as owner
            owner_membership = ProjectMember(
                project_id=project.id,
                user_id=creator_id,
                role=ProjectMemberRole.OWNER,
                invited_by=None  # Creator has no inviter
            )
            db.session.add(owner_membership)

            # Attach languages
            language_ids = data.get('language_ids') or []
            for lang_id in language_ids:
                project_lang = ProjectLanguage(
                    project_id=project.id,
                    language_id=lang_id
                )
                db.session.add(project_lang)

            db.session.commit()

            logger.info(
                f"Project created: id={project.id} title='{project.title}' "
                f"creator_id={creator_id} languages={language_ids}"
            )

            return True, "Project created successfully", project

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create project for creator_id={creator_id}: {e}")
            return False, "Failed to create project due to a server error", None

    # =========================================================================
    # FORK PROJECT
    # =========================================================================

    @staticmethod
    def fork_project(source_project_id, forking_user_id):
        """
        Fork an existing project. Creates a new project owned by forking_user
        with copied interest_tags and languages. Increments source fork_count.

        Forked project defaults: DRAFT + PRIVATE + REQUEST policy.
        These can be changed by the new owner before publishing.

        Guards:
            - Source project must exist
            - Source must be PUBLIC visibility
            - Source status must not be DRAFT or CANCELLED
            - Forking user must not be the source creator

        Args:
            source_project_id: Integer
            forking_user_id: Integer

        Returns:
            tuple: (success: bool, message: str, new_project: Project or None)
        """
        source = ProjectService._get_project_or_none(source_project_id)
        if not source:
            return False, "Project not found", None

        if source.visibility != ProjectVisibility.PUBLIC:
            return False, "Only public projects can be forked", None

        if source.status in (ProjectStatus.DRAFT, ProjectStatus.CANCELLED):
            return False, "Draft and cancelled projects cannot be forked", None

        if source.creator_id == forking_user_id:
            return False, "You cannot fork your own project", None

        try:
            # Collect source language IDs before creating new project
            source_language_ids = [pl.language_id for pl in source.languages]

            forked = Project(
                title=f"{source.title} (Fork)",
                description=source.description,
                creator_id=forking_user_id,
                status=ProjectStatus.DRAFT,
                membership_policy=MembershipPolicy.REQUEST,
                visibility=ProjectVisibility.PRIVATE,
                interest_tags=list(source.interest_tags or []),
                forked_from_id=source.id,
            )
            db.session.add(forked)
            db.session.flush()  # Obtain forked.id

            # Insert forking user as owner
            owner_membership = ProjectMember(
                project_id=forked.id,
                user_id=forking_user_id,
                role=ProjectMemberRole.OWNER,
                invited_by=None
            )
            db.session.add(owner_membership)

            # Copy languages
            for lang_id in source_language_ids:
                db.session.add(ProjectLanguage(
                    project_id=forked.id,
                    language_id=lang_id
                ))

            # Increment source fork_count (direct children only)
            source.fork_count += 1

            db.session.commit()

            logger.info(
                f"Project forked: source_id={source_project_id} "
                f"new_id={forked.id} forking_user_id={forking_user_id}"
            )

            return True, "Project forked successfully", forked

        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to fork project {source_project_id} "
                f"for user {forking_user_id}: {e}"
            )
            return False, "Failed to fork project due to a server error", None

    # =========================================================================
    # UPDATE PROJECT
    # =========================================================================

    @staticmethod
    def update_project(project_id, user_id, data):
        """
        Update project fields. Enforces state machine for status transitions.
        Only project owners may update.

        Args:
            project_id: Integer
            user_id: Integer — must be an owner
            data: Dict — any subset of:
                  title, description, membership_policy, visibility,
                  status, interest_tags, language_ids

        Returns:
            tuple: (success: bool, message: str, project: Project or None)
        """
        project = ProjectService._get_project_or_none(project_id)
        if not project:
            return False, "Project not found", None

        if not ProjectService._is_owner(project_id, user_id):
            return False, "Only project owners can update this project", None

        # Validate state transition if status is being changed
        new_status = data.get('status')
        if new_status is not None and new_status != project.status:
            allowed = VALID_TRANSITIONS.get(project.status, [])
            if new_status not in allowed:
                return False, (
                    f"Invalid transition: {project.status.value} → {new_status.value}. "
                    f"Allowed: {[s.value for s in allowed] or 'none'}"
                ), None

        try:
            # Apply scalar field updates
            if 'title' in data:
                title = data['title'].strip()
                if not title:
                    return False, "Project title cannot be empty", None
                if len(title) > 200:
                    return False, "Project title must be 200 characters or fewer", None
                project.title = title

            if 'description' in data:
                project.description = data['description']

            if 'membership_policy' in data:
                project.membership_policy = data['membership_policy']

            if 'visibility' in data:
                project.visibility = data['visibility']

            if 'interest_tags' in data:
                project.interest_tags = data['interest_tags'] or []

            if new_status is not None:
                project.status = new_status

            # Update timestamp explicitly — do not rely solely on onupdate
            project.updated_at = datetime.now(timezone.utc)

            # Handle language replacement if provided
            if 'language_ids' in data:
                # Remove existing language links
                ProjectLanguage.query.filter_by(project_id=project.id).delete()
                # Insert new ones
                for lang_id in (data['language_ids'] or []):
                    db.session.add(ProjectLanguage(
                        project_id=project.id,
                        language_id=lang_id
                    ))

            db.session.commit()

            # Award XP if project just moved to COMPLETED — after commit so a
            # failed XP award cannot roll back the status change.
            if new_status == ProjectStatus.COMPLETED:
                try:
                    ProjectService._award_completion_xp(project)
                except Exception as e:
                    logger.warning(
                        f"Non-fatal: _award_completion_xp failed for project_id={project_id}: {e}"
                    )

            logger.info(
                f"Project updated: id={project_id} by user_id={user_id} "
                f"new_status={new_status.value if new_status else 'unchanged'}"
            )

            return True, "Project updated successfully", project

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update project {project_id}: {e}")
            return False, "Failed to update project due to a server error", None

    # =========================================================================
    # MEMBERSHIP MANAGEMENT
    # =========================================================================

    @staticmethod
    def add_member(project_id, actor_id, target_user_id, role=None):
        """
        Add a user to a project. Outcome depends on project membership_policy.

        Policy resolution (service decides — routes must NOT pre-determine):
            - OPEN:   Insert target as CONTRIBUTOR immediately
            - REQUEST: Insert target as PENDING (requires approval)
            - INVITE:  Only allowed if actor is an OWNER; insert as CONTRIBUTOR

        Args:
            project_id: Integer
            actor_id: Integer — user performing the action (self-join or owner invite)
            target_user_id: Integer — user to add
            role: Ignored — role is determined by policy. Reserved for future use.

        Returns:
            tuple: (success: bool, message: str, member: ProjectMember or None)
        """
        project = ProjectService._get_project_or_none(project_id)
        if not project:
            return False, "Project not found", None

        # Check target user exists
        target = db.session.get(User, target_user_id)
        if not target:
            return False, "User not found", None

        # Check if already a member
        existing = ProjectService._get_member_or_none(project_id, target_user_id)
        if existing:
            return False, "User is already a member of this project", None

        # Resolve role from policy
        policy = project.membership_policy

        if policy == MembershipPolicy.OPEN:
            assigned_role = ProjectMemberRole.CONTRIBUTOR

        elif policy == MembershipPolicy.REQUEST:
            assigned_role = ProjectMemberRole.PENDING

        elif policy == MembershipPolicy.INVITE:
            if not ProjectService._is_owner(project_id, actor_id):
                return False, "This project is invite-only. Only owners can add members", None
            assigned_role = ProjectMemberRole.CONTRIBUTOR

        else:
            return False, "Unknown membership policy", None

        try:
            member = ProjectMember(
                project_id=project_id,
                user_id=target_user_id,
                role=assigned_role,
                invited_by=actor_id if actor_id != target_user_id else None
            )
            db.session.add(member)
            db.session.commit()

            # Award language XP if joining as active contributor
            if assigned_role == ProjectMemberRole.CONTRIBUTOR:
                ProjectService._award_contribution_xp(project, target_user_id)

            logger.info(
                f"Member added: project_id={project_id} user_id={target_user_id} "
                f"role={assigned_role.value} by actor_id={actor_id}"
            )

            return True, f"User added as {assigned_role.value}", member

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to add member to project {project_id}: {e}")
            return False, "Failed to add member due to a server error", None

    @staticmethod
    def approve_member(project_id, actor_id, pending_user_id):
        """
        Approve a pending join request. Promotes PENDING → CONTRIBUTOR.

        Args:
            project_id: Integer
            actor_id: Integer — must be an OWNER
            pending_user_id: Integer — must currently have role PENDING

        Returns:
            tuple: (success: bool, message: str, member: ProjectMember or None)
        """
        if not ProjectService._is_owner(project_id, actor_id):
            return False, "Only project owners can approve members", None

        member = ProjectService._get_member_or_none(project_id, pending_user_id)
        if not member:
            return False, "User is not a member of this project", None

        if member.role != ProjectMemberRole.PENDING:
            return False, "User does not have a pending join request", None

        try:
            member.role = ProjectMemberRole.CONTRIBUTOR
            db.session.commit()

            # Award language XP now that they are an active contributor
            project = ProjectService._get_project_or_none(project_id)
            if project:
                ProjectService._award_contribution_xp(project, pending_user_id)

            logger.info(
                f"Member approved: project_id={project_id} "
                f"user_id={pending_user_id} by actor_id={actor_id}"
            )

            return True, "Member approved as contributor", member

        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to approve member {pending_user_id} "
                f"in project {project_id}: {e}"
            )
            return False, "Failed to approve member due to a server error", None

    @staticmethod
    def promote_to_owner(project_id, actor_id, target_user_id):
        """
        Promote an existing member to OWNER role.
        Actor must be an owner. Target must be an existing member (any role).

        Args:
            project_id: Integer
            actor_id: Integer — must be an OWNER
            target_user_id: Integer

        Returns:
            tuple: (success: bool, message: str, member: ProjectMember or None)
        """
        if not ProjectService._is_owner(project_id, actor_id):
            return False, "Only project owners can promote members", None

        if actor_id == target_user_id:
            return False, "You are already an owner", None

        member = ProjectService._get_member_or_none(project_id, target_user_id)
        if not member:
            return False, "User is not a member of this project", None

        if member.role == ProjectMemberRole.OWNER:
            return False, "User is already an owner", None

        try:
            member.role = ProjectMemberRole.OWNER
            db.session.commit()

            logger.info(
                f"Member promoted to owner: project_id={project_id} "
                f"user_id={target_user_id} by actor_id={actor_id}"
            )

            return True, "Member promoted to owner", member

        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to promote member {target_user_id} "
                f"in project {project_id}: {e}"
            )
            return False, "Failed to promote member due to a server error", None

    @staticmethod
    def remove_member(project_id, actor_id, target_user_id):
        """
        Remove a member from a project.

        Guard: Cannot remove the last owner — project would become ownerless.
        Owners can remove any member. Members can remove themselves (self-leave).

        Args:
            project_id: Integer
            actor_id: Integer — owner, or same as target_user_id (self-leave)
            target_user_id: Integer

        Returns:
            tuple: (success: bool, message: str)
        """
        project = ProjectService._get_project_or_none(project_id)
        if not project:
            return False, "Project not found"

        member = ProjectService._get_member_or_none(project_id, target_user_id)
        if not member:
            return False, "User is not a member of this project"

        is_self_leave = (actor_id == target_user_id)
        is_actor_owner = ProjectService._is_owner(project_id, actor_id)

        if not is_self_leave and not is_actor_owner:
            return False, "Only project owners can remove other members"

        # Last-owner guard — checked and acted on within the same transaction
        if member.role == ProjectMemberRole.OWNER:
            if ProjectService._owner_count(project_id) <= 1:
                return False, (
                    "Cannot remove the last owner. "
                    "Promote another member to owner first."
                )

        try:
            db.session.delete(member)
            db.session.commit()

            logger.info(
                f"Member removed: project_id={project_id} "
                f"user_id={target_user_id} by actor_id={actor_id}"
            )

            return True, "Member removed successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to remove member {target_user_id} "
                f"from project {project_id}: {e}"
            )
            return False, "Failed to remove member due to a server error"

    # =========================================================================
    # DISCOVERY
    # =========================================================================

    @staticmethod
    def discover_projects(user_id, limit=50):
        """
        Return ranked list of projects for a user based on interest overlap.

        Algorithm:
            1. Fetch user's interest_scores from user_scorings (JSONB dict)
            2. Filter projects: PUBLIC visibility, status IN (OPEN, IN_PROGRESS)
            3. For each candidate project, compute overlap_score =
               SUM of user's interest score for each matching tag
            4. Sort by overlap_score DESC, return top `limit` results

        Note: DB-level filter runs first (steps 1–2). Python overlap scoring
        runs only on the filtered candidate set — not the entire projects table.

        Args:
            user_id: Integer
            limit: Integer — max results to return (default 50)

        Returns:
            tuple: (success: bool, message: str, projects: list of dict or None)
        """
        from app.models.scoring import UserScoring

        try:
            # Fetch user's interest scores
            scoring = UserScoring.query.filter_by(user_id=user_id).first()
            user_interest_scores = {}
            if scoring and scoring.interest_scores:
                user_interest_scores = scoring.interest_scores  # Dict: {tag: score}

            # DB-level filter — do NOT pull all projects into memory
            candidates = Project.query.filter(
                Project.visibility == ProjectVisibility.PUBLIC,
                Project.status.in_([ProjectStatus.OPEN, ProjectStatus.IN_PROGRESS])
            ).all()

            # Score each candidate in Python (filtered set only)
            scored = []
            for project in candidates:
                tags = project.interest_tags or []
                overlap_score = sum(
                    user_interest_scores.get(tag, 0.0)
                    for tag in tags
                )
                scored.append((overlap_score, project))

            # Sort by overlap score descending
            scored.sort(key=lambda x: x[0], reverse=True)

            results = [
                {
                    'project': project,
                    'overlap_score': round(score, 2)
                }
                for score, project in scored[:limit]
            ]

            logger.info(
                f"Discovery: user_id={user_id} candidates={len(candidates)} "
                f"returned={len(results)}"
            )

            return True, "Projects discovered successfully", results

        except Exception as e:
            logger.error(f"Failed to run discovery for user_id={user_id}: {e}")
            return False, "Failed to retrieve projects", None

    # =========================================================================
    # INTERNAL XP HELPERS
    # =========================================================================

    @staticmethod
    def _award_contribution_xp(project, user_id):
        """
        Award language XP to a user for joining a project as contributor.
        Called after membership is committed — does not affect the main transaction.

        Failures are logged but do not raise — XP is supplementary.
        """
        language_ids = [pl.language_id for pl in project.languages]
        language_names = ProjectService._resolve_language_names(language_ids)

        for lang_name in language_names:
            try:
                _lang_service.add_language_xp(
                    user_id=user_id,
                    language_name=lang_name,
                    activity_type='project_contribution'
                )
            except Exception as e:
                logger.warning(
                    f"Could not award contribution XP for lang={lang_name} "
                    f"user_id={user_id}: {e}"
                )

    @staticmethod
    def _award_completion_xp(project):
        """
        Award XP to all active members when a project reaches COMPLETED.
        Uses XPService for general XP and LanguageProficiencyService for language XP.

        Failures are logged but do not raise — XP is supplementary.
        Called inside update_project() before commit.
        """
        active_roles = [ProjectMemberRole.OWNER, ProjectMemberRole.CONTRIBUTOR]
        active_members = ProjectMember.query.filter(
            ProjectMember.project_id == project.id,
            ProjectMember.role.in_(active_roles)
        ).all()

        language_ids = [pl.language_id for pl in project.languages]
        language_names = ProjectService._resolve_language_names(language_ids)

        for member in active_members:
            user = db.session.get(User, member.user_id)
            if not user:
                continue

            # General XP via XPService — amount from XP_AMOUNTS['project_submit']
            try:
                XPService.award_xp(
                    user=user,
                    amount=XP_AMOUNTS.get('project_submit', 150),
                    source='project_completed',
                    description=f"Project '{project.title}' completed",
                    related_entity_type='Project',
                    related_entity_id=project.id
                )
            except Exception as e:
                logger.warning(
                    f"Could not award completion XP to user_id={member.user_id}: {e}"
                )

            # Language proficiency XP
            for lang_name in language_names:
                try:
                    _lang_service.add_language_xp(
                        user_id=member.user_id,
                        language_name=lang_name,
                        activity_type='project_contribution'
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not award completion lang XP for lang={lang_name} "
                        f"user_id={member.user_id}: {e}"
                    )


# Singleton instance — consistent with existing service pattern
project_service = ProjectService()
