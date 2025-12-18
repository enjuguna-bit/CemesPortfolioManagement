"""
Chunked file upload endpoints for mobile optimization
Supports large file uploads with progress tracking
"""
from flask import Blueprint, request, jsonify, g, current_app
from middleware.auth import require_auth
from middleware.error_handler import ValidationError, NotFoundError
from utils.validators import validate_file, sanitize_filename
from database import db
from models.upload_session import UploadSession
import os
import uuid
import logging

logger = logging.getLogger(__name__)

uploads_bp = Blueprint('uploads', __name__)


@uploads_bp.route('/initiate', methods=['POST'])
@require_auth
def initiate_upload():
    """
    Initiate chunked file upload session
    
    Request body:
    {
        "filename": "string",
        "file_size": integer,
        "total_chunks": integer,
        "content_type": "string" (optional),
        "metadata": object (optional)
    }
    
    Returns:
        Upload session information
    """
    data = request.get_json()
    
    # Validate required fields
    required = ['filename', 'file_size', 'total_chunks']
    missing = [f for f in required if f not in data]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")
    
    # Validate file size
    max_size = current_app.config['MAX_CONTENT_LENGTH']
    if data['file_size'] > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValidationError(f'File too large. Maximum size: {max_mb:.1f}MB')
    
    # Sanitize filename
    filename = sanitize_filename(data['filename'])
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Create upload session
    session = UploadSession(
        session_id=session_id,
        user_id=g.user_id,
        filename=filename,
        file_size=data['file_size'],
        total_chunks=data['total_chunks'],
        content_type=data.get('content_type'),
        metadata=data.get('metadata', {})
    )
    
    db.session.add(session)
    db.session.commit()
    
    logger.info(f"Upload session initiated: {session_id}")
    
    return jsonify({
        'success': True,
        'data': session.to_dict(),
        'message': 'Upload session initiated'
    }), 201


@uploads_bp.route('/chunk', methods=['POST'])
@require_auth
def upload_chunk():
    """
    Upload file chunk
    
    Headers:
        X-Upload-Id: Upload session ID
        X-Chunk-Number: Chunk number (1-indexed)
    
    Form data:
        chunk: File chunk data
    """
    # Get session ID and chunk number from headers
    session_id = request.headers.get('X-Upload-Id')
    chunk_number = request.headers.get('X-Chunk-Number')
    
    if not session_id or not chunk_number:
        raise ValidationError('X-Upload-Id and X-Chunk-Number headers are required')
    
    try:
        chunk_number = int(chunk_number)
    except ValueError:
        raise ValidationError('X-Chunk-Number must be an integer')
    
    # Get upload session
    session = UploadSession.query.filter_by(session_id=session_id).first()
    
    if not session:
        raise NotFoundError('Upload session not found')
    
    # Verify ownership
    if session.user_id != g.user_id:
        from middleware.error_handler import AuthorizationError
        raise AuthorizationError('Not authorized to upload to this session')
    
    # Check if session is expired
    if session.is_expired():
        raise ValidationError('Upload session has expired')
    
    # Get chunk file
    if 'chunk' not in request.files:
        raise ValidationError('No chunk file provided')
    
    chunk_file = request.files['chunk']
    
    # Create session directory if it doesn't exist
    upload_folder = current_app.config['UPLOAD_FOLDER']
    session_dir = os.path.join(upload_folder, session_id)
    
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    
    # Save chunk
    chunk_path = os.path.join(session_dir, f'chunk_{chunk_number}')
    chunk_file.save(chunk_path)
    
    # Mark chunk as uploaded
    session.add_chunk(chunk_number)
    
    logger.info(f"Chunk {chunk_number} uploaded for session {session_id}")
    
    return jsonify({
        'success': True,
        'data': {
            'session_id': session_id,
            'chunk_number': chunk_number,
            'progress': session.get_progress(),
            'is_complete': session.is_complete()
        },
        'message': f'Chunk {chunk_number} uploaded successfully'
    })


@uploads_bp.route('/complete', methods=['POST'])
@require_auth
def complete_upload():
    """
    Complete chunked upload and merge chunks
    
    Request body:
    {
        "session_id": "string"
    }
    
    Returns:
        Final file information
    """
    data = request.get_json()
    
    if not data.get('session_id'):
        raise ValidationError('session_id is required')
    
    session_id = data['session_id']
    
    # Get upload session
    session = UploadSession.query.filter_by(session_id=session_id).first()
    
    if not session:
        raise NotFoundError('Upload session not found')
    
    # Verify ownership
    if session.user_id != g.user_id:
        from middleware.error_handler import AuthorizationError
        raise AuthorizationError('Not authorized to complete this upload')
    
    # Check if all chunks are uploaded
    if not session.is_complete():
        raise ValidationError(
            f'Upload incomplete. {len(session.uploaded_chunks or [])}/{session.total_chunks} chunks uploaded'
        )
    
    # Merge chunks
    upload_folder = current_app.config['UPLOAD_FOLDER']
    session_dir = os.path.join(upload_folder, session_id)
    final_path = os.path.join(upload_folder, f'{session_id}_{session.filename}')
    
    try:
        with open(final_path, 'wb') as final_file:
            for chunk_num in sorted(session.uploaded_chunks):
                chunk_path = os.path.join(session_dir, f'chunk_{chunk_num}')
                with open(chunk_path, 'rb') as chunk_file:
                    final_file.write(chunk_file.read())
        
        # Clean up chunk files
        import shutil
        shutil.rmtree(session_dir)
        
        # Mark session as completed
        session.mark_completed(final_path)
        
        logger.info(f"Upload completed for session {session_id}")
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id,
                'filename': session.filename,
                'file_size': session.file_size,
                'storage_path': final_path
            },
            'message': 'Upload completed successfully'
        })
    
    except Exception as e:
        session.mark_failed()
        logger.error(f"Error completing upload {session_id}: {str(e)}")
        raise ValidationError(f'Failed to complete upload: {str(e)}')


@uploads_bp.route('/<session_id>', methods=['DELETE'])
@require_auth
def cancel_upload(session_id):
    """
    Cancel upload session and clean up chunks
    """
    session = UploadSession.query.filter_by(session_id=session_id).first()
    
    if not session:
        raise NotFoundError('Upload session not found')
    
    # Verify ownership
    if session.user_id != g.user_id:
        from middleware.error_handler import AuthorizationError
        raise AuthorizationError('Not authorized to cancel this upload')
    
    # Clean up chunks
    upload_folder = current_app.config['UPLOAD_FOLDER']
    session_dir = os.path.join(upload_folder, session_id)
    
    if os.path.exists(session_dir):
        import shutil
        shutil.rmtree(session_dir)
    
    # Mark as failed
    session.mark_failed()
    
    logger.info(f"Upload cancelled for session {session_id}")
    
    return jsonify({
        'success': True,
        'message': 'Upload cancelled successfully'
    })


@uploads_bp.route('/<session_id>', methods=['GET'])
@require_auth
def get_upload_status(session_id):
    """
    Get upload session status and progress
    """
    session = UploadSession.query.filter_by(session_id=session_id).first()
    
    if not session:
        raise NotFoundError('Upload session not found')
    
    # Verify ownership
    if session.user_id != g.user_id:
        from middleware.error_handler import AuthorizationError
        raise AuthorizationError('Not authorized to view this upload')
    
    return jsonify({
        'success': True,
        'data': session.to_dict()
    })
