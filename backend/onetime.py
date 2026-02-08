# Run this Python script to update existing communities
from app import create_app, db
from app.models.community import Community

app = create_app()
with app.app_context():
    communities = Community.query.all()
    
    for community in communities:
        # Set default values for new fields
        if community.max_members is None:
            community.max_members = 50
        if community.current_member_count is None:
            # Count current members
            from app.models.community_member import CommunityMember
            count = CommunityMember.query.filter_by(
                community_id=community.community_id
            ).count()
            community.current_member_count = count
        if community.is_college_specific is None:
            community.is_college_specific = True
        if community.programming_languages is None:
            community.programming_languages = []
    
    db.session.commit()
    print(f"Updated {len(communities)} communities")