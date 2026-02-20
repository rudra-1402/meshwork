from app.extensions import db
from datetime import datetime, timezone
from sqlalchemy.orm import validates


class CommunityFile(db.Model):
    """
    Files shared in communities.
    """
    __tablename__ = "community_files"

    file_id = db.Column(db.Integer, primary_key=True)
    
    community_id = db.Column(
        db.Integer,
        db.ForeignKey("communities.community_id"),
        nullable=False
    )
    
    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    
    # File metadata
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)  # Path on server/S3
    file_size = db.Column(db.Integer, nullable=False)  # Bytes
    mime_type = db.Column(db.String(100), nullable=False)
    
    # File description
    description = db.Column(db.Text, nullable=True)
    
    # File category: "document", "image", "code", "other"
    category = db.Column(db.String(20), default="other")
    
    # Download count
    download_count = db.Column(db.Integer, default=0)
    
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    # ===== Relationships =====
    community = db.relationship("Community", backref="files")
    uploader = db.relationship("User", backref="uploaded_files")

    __table_args__ = (
        db.Index('idx_community_files_community_id', 'community_id'),
        db.Index('idx_community_files_uploaded_by', 'uploaded_by'),
    )

    @validates('file_path')
    def validate_file_path(self, key, value):
        if value and ('..' in value or value.startswith('/')):
            raise ValueError("Invalid file path")
        return value

    def __repr__(self):
        return f"<CommunityFile '{self.original_filename}'>"
    
    def increment_download(self):
        """Increment download counter"""
        self.download_count += 1
    
    def get_file_size_human(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
