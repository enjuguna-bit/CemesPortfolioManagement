"""
User model for authentication and authorization
"""
from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """User model for authentication"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200))
    
    # Role-based access control
    roles = db.Column(db.JSON, default=list)  # List of role strings
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    devices = db.relationship('Device', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, username, email, password, full_name=None, roles=None):
        self.username = username
        self.email = email
        self.set_password(password)
        self.full_name = full_name
        self.roles = roles or ['user']
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        """Check if user has specific role"""
        return role in (self.roles or [])
    
    def add_role(self, role):
        """Add role to user"""
        if not self.roles:
            self.roles = []
        if role not in self.roles:
            self.roles.append(role)
            db.session.commit()
    
    def remove_role(self, role):
        """Remove role from user"""
        if self.roles and role in self.roles:
            self.roles.remove(role)
            db.session.commit()
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'roles': self.roles,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'
