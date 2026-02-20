from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.college import College
from app.models.project import Project, ProjectStatus, MembershipPolicy, ProjectVisibility

def insert_dummy_data():
    app = create_app()
    with app.app_context():
        # Insert dummy colleges
        college1 = College(
            name="Tech University",
            email="info@techuniversity.edu",
            city="Tech City",
            state="Tech State",
            address="123 Tech Street",
            domain="techuniversity.edu",
            student_email_pattern="*@student.techuniversity.edu",
            personnel_email_pattern="*@staff.techuniversity.edu",
            registration_number="TU-12345",
        )
        college1.set_password("password123")
        db.session.add(college1)

        # Insert dummy users
        user1 = User(
            username="john_doe",
            first_name="John",
            last_name="Doe",
            email="john.doe@student.techuniversity.edu",
            college=college1,
            is_admin=False,
            xp=150,
            level=2,
            reputation=10,
            current_streak=3,
            max_streak=5
        )
        user1.set_password("password123")
        db.session.add(user1)

        user2 = User(
            username="jane_smith",
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@student.techuniversity.edu",
            college=college1,
            is_admin=True,
            xp=500,
            level=3,
            reputation=20,
            current_streak=7,
            max_streak=10
        )
        user2.set_password("password123")
        db.session.add(user2)

        # Insert dummy projects
        project1 = Project(
            title="AI Research Project",
            description="A project focused on developing AI models for image recognition.",
            creator=user1,
            status=ProjectStatus.IN_PROGRESS,
            membership_policy=MembershipPolicy.OPEN,
            visibility=ProjectVisibility.PUBLIC,
            interest_tags=["AI", "Machine Learning", "Image Recognition"]
        )
        db.session.add(project1)

        project2 = Project(
            title="Web Development Bootcamp",
            description="A project to create a website for local businesses.",
            creator=user2,
            status=ProjectStatus.OPEN,
            membership_policy=MembershipPolicy.REQUEST,
            visibility=ProjectVisibility.PUBLIC,
            interest_tags=["Web Development", "UI/UX Design"]
        )
        db.session.add(project2)

        # Commit changes
        db.session.commit()
        print("Dummy data inserted successfully.")

if __name__ == "__main__":
    insert_dummy_data()