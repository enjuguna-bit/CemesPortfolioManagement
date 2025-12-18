"""
Device model for Android device registration and FCM token management
"""
from database import db
from datetime import datetime


class Device(db.Model):
    """Device model for mobile device registration"""
    
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # User association
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Device information
    platform = db.Column(db.String(50), default='android')  # android, ios, web
    device_name = db.Column(db.String(200))
    device_model = db.Column(db.String(200))
    os_version = db.Column(db.String(50))
    app_version = db.Column(db.String(50))
    
    # FCM token for push notifications
    fcm_token = db.Column(db.String(500))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Sync information
    last_sync = db.Column(db.DateTime)
    sync_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, device_id, user_id, platform='android', fcm_token=None, **kwargs):
        self.device_id = device_id
        self.user_id = user_id
        self.platform = platform
        self.fcm_token = fcm_token
        
        # Set optional fields
        self.device_name = kwargs.get('device_name')
        self.device_model = kwargs.get('device_model')
        self.os_version = kwargs.get('os_version')
        self.app_version = kwargs.get('app_version')
    
    def update_fcm_token(self, token):
        """Update FCM token"""
        self.fcm_token = token
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_sync(self):
        """Update last sync timestamp"""
        self.last_sync = datetime.utcnow()
        self.sync_count += 1
        db.session.commit()
    
    def deactivate(self):
        """Deactivate device"""
        self.is_active = False
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'platform': self.platform,
            'device_name': self.device_name,
            'device_model': self.device_model,
            'os_version': self.os_version,
            'app_version': self.app_version,
            'is_active': self.is_active,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None
        }
    
    def __repr__(self):
        return f'<Device {self.device_id} ({self.platform})>'
