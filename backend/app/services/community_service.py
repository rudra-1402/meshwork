from app.extensions import db
from app.models.community import Community
from app.models.community_member import CommunityMember


def create_community_service(
    community_name,
    subject,
    college_id,
    user_id
):
    """
    Creates a community and adds creator as admin member
    """

    # 1️⃣ Create community
    community = Community(
        community_name=community_name,
        subject=subject,
        college_id=college_id,
        created_by=user_id
    )

    db.session.add(community)
    db.session.flush()  # get community_id before commit

    # 2️⃣ Add creator as first member (admin)
    member = CommunityMember(
        user_id=user_id,
        community_id=community.community_id
    )

    db.session.add(member)
    db.session.commit()

    return community
