"""
factory-boy model factories for test data generation.
"""
import factory
from factory.alchemy import SQLAlchemyModelFactory
from app.extensions import db
from app.models.user import User
from app.models.project import Project, ProjectStatus, MembershipPolicy, ProjectVisibility
from app.models.college import College
from app.models.college_personnel import CollegePersonnel
from app.models.community import Community
from app.models.community_member import CommunityMember
from app.models.community_message import CommunityMessage
from app.models.community_poll import CommunityPoll, PollVote
from app.models.community_task import CommunityTask
from app.models.language import Language
from app.models.user_language import UserLanguage
from app.models.user_skill import UserSkill


class CollegeFactory(SQLAlchemyModelFactory):
    class Meta:
        model = College
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: f"Test College {n}")
    email = factory.Sequence(lambda n: f"college_{n}@edu")
    domain = factory.Sequence(lambda n: f"college{n}.edu")
    student_email_pattern = factory.LazyAttribute(lambda obj: f"*@{obj.domain}")
    personnel_email_pattern = factory.LazyAttribute(lambda obj: f"*@staff.{obj.domain}")
    city = factory.Faker("city")
    state = factory.Faker("state")
    address = factory.Faker("address")
    registration_number = factory.Sequence(lambda n: f"REG{n:05d}")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.set_password("CollegePass123!")
        db.session.add(obj)
        db.session.commit()
        return obj


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@student.edu")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    # Don't auto-create college - let tests specify if needed
    # college = factory.SubFactory(CollegeFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.set_password("TestPass123!")
        db.session.add(obj)
        db.session.commit()
        return obj


class PersonnelFactory(SQLAlchemyModelFactory):
    class Meta:
        model = CollegePersonnel
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Sequence(lambda n: f"personnel_{n}@college.edu")
    role = "faculty"
    personnel_id = factory.Sequence(lambda n: f"PER{n:05d}")
    is_active = True
    can_manage_students = False
    can_manage_personnel = False
    college = factory.SubFactory(CollegeFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.set_password("TestPass123!")
        db.session.add(obj)
        db.session.commit()
        return obj


class ProjectFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Project
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    title = factory.Sequence(lambda n: f"Project {n}")
    description = factory.Faker("paragraph")
    creator = factory.SubFactory(UserFactory)
    status = ProjectStatus.OPEN
    membership_policy = MembershipPolicy.REQUEST
    visibility = ProjectVisibility.PUBLIC
    interest_tags = []
    fork_count = 0


class CommunityFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Community
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    community_name = factory.Sequence(lambda n: f"Community {n}")
    subject = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph")
    # created_by and college_id should be specified by the test
    # created_by = factory.SubFactory(UserFactory)
    # college = factory.SubFactory(CollegeFactory)
    max_members = 50
    current_member_count = 0
    is_college_specific = True
    programming_languages = ["Python", "JavaScript"]
    is_active = True
    is_archived = False


class CommunityMemberFactory(SQLAlchemyModelFactory):
    class Meta:
        model = CommunityMember
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    # user and community should be specified by the test
    # user = factory.SubFactory(UserFactory)
    # community = factory.SubFactory(CommunityFactory)


class CommunityMessageFactory(SQLAlchemyModelFactory):
    class Meta:
        model = CommunityMessage
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    # community and user should be specified by the test
    # community = factory.SubFactory(CommunityFactory)
    # user = factory.SubFactory(UserFactory)
    message_text = factory.Faker("paragraph")
    is_deleted = False


class CommunityPollFactory(SQLAlchemyModelFactory):
    class Meta:
        model = CommunityPoll
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    # community and created_by should be specified by the test
    # community = factory.SubFactory(CommunityFactory)
    # created_by = factory.SubFactory(UserFactory)
    question = factory.Faker("sentence")
    options = ["Option A", "Option B", "Option C"]
    is_active = True
    is_deleted = False


class PollVoteFactory(SQLAlchemyModelFactory):
    class Meta:
        model = PollVote
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    # poll and user should be specified by the test
    # poll = factory.SubFactory(CommunityPollFactory)
    # user = factory.SubFactory(UserFactory)
    selected_option = "Option A"


class CommunityTaskFactory(SQLAlchemyModelFactory):
    class Meta:
        model = CommunityTask
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    # community and created_by should be specified by the test
    # community = factory.SubFactory(CommunityFactory)
    # created_by = factory.SubFactory(UserFactory)
    task_title = factory.Faker("sentence")
    task_description = factory.Faker("paragraph")
    xp_reward = 50
    is_completed = False


class LanguageFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Language
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: f"Language{n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower())


class UserLanguageFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UserLanguage
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    # user and language should be specified by the test
    # user = factory.SubFactory(UserFactory)
    # language = factory.SubFactory(LanguageFactory)
    proficiency_level = 3


class UserSkillFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UserSkill
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    # user should be specified by the test
    # user = factory.SubFactory(UserFactory)
    skill_name = factory.Faker("job")
    xp = 0
    level = 0
