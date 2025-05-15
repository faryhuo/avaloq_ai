from flask import Blueprint, jsonify, request, send_from_directory
import os
from werkzeug.utils import secure_filename
import shutil

file_manager = Blueprint('file_manager', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'md'}
FILES_FOLDER = 'files'
DOC_FOLDER = 'doc'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@file_manager.route('/api/files', methods=['GET'])
def list_files():
    """List files in the files directory (only first level)"""
    files_list = []
    for item in os.listdir(FILES_FOLDER):
        item_path = os.path.join(FILES_FOLDER, item)
        if os.path.isfile(item_path):  # Only include files, not directories
            files_list.append({
                'name': item,
                'size': os.path.getsize(item_path),
                'modified': os.path.getmtime(item_path)
            })
    return jsonify(files_list)

@file_manager.route('/api/docs', methods=['GET'])
def list_docs():
    """List markdown files in the doc directory"""
    docs_list = []
    for item in os.listdir(DOC_FOLDER):
        item_path = os.path.join(DOC_FOLDER, item)
        if os.path.isfile(item_path) and item.lower().endswith('.md'):
            docs_list.append({
                'name': item,
                'size': os.path.getsize(item_path),
                'modified': os.path.getmtime(item_path)
            })
    return jsonify(docs_list)

@file_manager.route('/api/upload/<folder>', methods=['POST'])
def upload_file(folder):
    """Upload a file to either files or doc folder"""
    if folder not in ['files', 'doc']:
        return jsonify({'error': 'Invalid folder'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # For doc folder, only allow markdown files
        if folder == 'doc' and not filename.lower().endswith('.md'):
            return jsonify({'error': 'Only markdown files are allowed in doc folder'}), 400
        
        upload_folder = FILES_FOLDER if folder == 'files' else DOC_FOLDER
        file.save(os.path.join(upload_folder, filename))
        return jsonify({'message': 'File uploaded successfully'})
    
    return jsonify({'error': 'File type not allowed'}), 400

@file_manager.route('/api/delete/<folder>/<filename>', methods=['DELETE'])
def delete_file(folder, filename):
    """Delete a file from either files or doc folder"""
    if folder not in ['files', 'doc']:
        return jsonify({'error': 'Invalid folder'}), 400
    
    target_folder = FILES_FOLDER if folder == 'files' else DOC_FOLDER
    file_path = os.path.join(target_folder, secure_filename(filename))
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        os.remove(file_path)
        return jsonify({'message': 'File deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@file_manager.route('/api/download/<folder>/<filename>')
def download_file(folder, filename):
    """Download a file from either files or doc folder"""
    if folder not in ['files', 'doc']:
        return jsonify({'error': 'Invalid folder'}), 400
    
    target_folder = FILES_FOLDER if folder == 'files' else DOC_FOLDER
    return send_from_directory(target_folder, secure_filename(filename)) 