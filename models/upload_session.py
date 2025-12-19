"""
Upload session model for chunked file uploads
"""
from database import db
from datetime import datetime, timedelta
import json


class UploadSession(db.Model):
    """Upload session model for chunked file uploads"""
    
    __tablename__ = 'upload_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # User association
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # File information
    filename = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)  # Total file size in bytes
    content_type = db.Column(db.String(100))
    
    # Chunk tracking
    total_chunks = db.Column(db.Integer)
    uploaded_chunks = db.Column(db.JSON, default=list)  # List of uploaded chunk numbers
    chunk_size = db.Column(db.Integer, default=1048576)  # 1MB default
    
    # Storage
    storage_path = db.Column(db.String(1000))  # Temporary storage path
    
    # Status
    status = db.Column(db.String(50), default='initiated')  # initiated, uploading, completed, failed, expired
    
    # Metadata
    upload_metadata = db.Column(db.JSON, default=dict)  # Additional metadata
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime)
    
    def __init__(self, session_id, user_id, filename, file_size=None, total_chunks=None, **kwargs):
        self.session_id = session_id
        self.user_id = user_id
        self.filename = filename
        self.file_size = file_size
        self.total_chunks = total_chunks
        
        # Set expiration (24 hours from now)
        self.expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Set optional fields
        self.content_type = kwargs.get('content_type')
        self.chunk_size = kwargs.get('chunk_size', 1048576)
        self.upload_metadata = kwargs.get('metadata', {})
    
    def add_chunk(self, chunk_number):
        """Mark chunk as uploaded"""
        if not self.uploaded_chunks:
            self.uploaded_chunks = []
        
        if chunk_number not in self.uploaded_chunks:
            self.uploaded_chunks.append(chunk_number)
            self.status = 'uploading'
            self.updated_at = datetime.utcnow()
            db.session.commit()
    
    def is_complete(self):
        """Check if all chunks are uploaded"""
        if not self.total_chunks or not self.uploaded_chunks:
            return False
        
        return len(self.uploaded_chunks) >= self.total_chunks
    
    def mark_completed(self, storage_path):
        """Mark upload as completed"""
        self.status = 'completed'
        self.storage_path = storage_path
        self.completed_at = datetime.utcnow()
        db.session.commit()
    
    def mark_failed(self):
        """Mark upload as failed"""
        self.status = 'failed'
        db.session.commit()
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def get_progress(self):
        """Get upload progress percentage"""
        if not self.total_chunks:
            return 0
        
        return (len(self.uploaded_chunks or []) / self.total_chunks) * 100
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'session_id': self.session_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'total_chunks': self.total_chunks,
            'uploaded_chunks': len(self.uploaded_chunks or []),
            'progress': self.get_progress(),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    def __repr__(self):
        return f'<UploadSession {self.session_id} ({self.status})>'
