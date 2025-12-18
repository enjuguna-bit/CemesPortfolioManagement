"""
Device management endpoints for Android device registration and FCM
"""
from flask import Blueprint, request, jsonify, g
from middleware.auth import require_auth
from middleware.error_handler import ValidationError, NotFoundError
from database import db
from models.device import Device
import logging

logger = logging.getLogger(__name__)

devices_bp = Blueprint('devices', __name__)


@devices_bp.route('/register', methods=['POST'])
@require_auth
def register_device():
    """
    Register Android device with FCM token
    
    Request body:
    {
        "device_id": "string",
        "platform": "android",
        "fcm_token": "string",
        "device_name": "string" (optional),
        "device_model": "string" (optional),
        "os_version": "string" (optional),
        "app_version": "string" (optional)
    }
    
    Returns:
        Device information
    """
    data = request.get_json()
    
    # Validate required fields
    if not data.get('device_id'):
        raise ValidationError('Device ID is required', field='device_id')
    
    # Check if device already exists
    device = Device.query.filter_by(device_id=data['device_id']).first()
    
    if device:
        # Update existing device
        device.fcm_token = data.get('fcm_token', device.fcm_token)
        device.device_name = data.get('device_name', device.device_name)
        device.device_model = data.get('device_model', device.device_model)
        device.os_version = data.get('os_version', device.os_version)
        device.app_version = data.get('app_version', device.app_version)
        device.is_active = True
        
        logger.info(f"Device updated: {device.device_id}")
        message = 'Device updated successfully'
    else:
        # Create new device
        device = Device(
            device_id=data['device_id'],
            user_id=g.user_id,
            platform=data.get('platform', 'android'),
            fcm_token=data.get('fcm_token'),
            device_name=data.get('device_name'),
            device_model=data.get('device_model'),
            os_version=data.get('os_version'),
            app_version=data.get('app_version')
        )
        db.session.add(device)
        
        logger.info(f"New device registered: {device.device_id}")
        message = 'Device registered successfully'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': device.to_dict(),
        'message': message
    }), 201 if not device.id else 200


@devices_bp.route('/<int:device_id>', methods=['PUT'])
@require_auth
def update_device(device_id):
    """
    Update device information
    
    Request body:
    {
        "fcm_token": "string" (optional),
        "device_name": "string" (optional),
        "app_version": "string" (optional)
    }
    """
    device = Device.query.get(device_id)
    
    if not device:
        raise NotFoundError('Device not found')
    
    # Verify ownership
    if device.user_id != g.user_id:
        from middleware.error_handler import AuthorizationError
        raise AuthorizationError('Not authorized to update this device')
    
    data = request.get_json()
    
    # Update fields
    if 'fcm_token' in data:
        device.update_fcm_token(data['fcm_token'])
    
    if 'device_name' in data:
        device.device_name = data['device_name']
    
    if 'app_version' in data:
        device.app_version = data['app_version']
    
    db.session.commit()
    
    logger.info(f"Device updated: {device.device_id}")
    
    return jsonify({
        'success': True,
        'data': device.to_dict(),
        'message': 'Device updated successfully'
    })


@devices_bp.route('/<int:device_id>', methods=['DELETE'])
@require_auth
def unregister_device(device_id):
    """
    Unregister device
    """
    device = Device.query.get(device_id)
    
    if not device:
        raise NotFoundError('Device not found')
    
    # Verify ownership
    if device.user_id != g.user_id:
        from middleware.error_handler import AuthorizationError
        raise AuthorizationError('Not authorized to delete this device')
    
    device.deactivate()
    
    logger.info(f"Device unregistered: {device.device_id}")
    
    return jsonify({
        'success': True,
        'message': 'Device unregistered successfully'
    })


@devices_bp.route('/', methods=['GET'])
@require_auth
def list_devices():
    """
    List all devices for current user
    
    Returns:
        List of user's devices
    """
    devices = Device.query.filter_by(user_id=g.user_id, is_active=True).all()
    
    return jsonify({
        'success': True,
        'data': [device.to_dict() for device in devices]
    })


@devices_bp.route('/<int:device_id>/sync', methods=['POST'])
@require_auth
def update_sync(device_id):
    """
    Update device sync timestamp
    
    Called by Android app after successful background sync
    """
    device = Device.query.get(device_id)
    
    if not device:
        raise NotFoundError('Device not found')
    
    # Verify ownership
    if device.user_id != g.user_id:
        from middleware.error_handler import AuthorizationError
        raise AuthorizationError('Not authorized to update this device')
    
    device.update_sync()
    
    return jsonify({
        'success': True,
        'data': {
            'last_sync': device.last_sync.isoformat() if device.last_sync else None,
            'sync_count': device.sync_count
        },
        'message': 'Sync updated successfully'
    })
