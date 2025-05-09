from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_restx import Api, Resource, fields
import os
import difflib
from html import escape
import uuid
from datetime import datetime
import re
import threading
import time
from pathlib import Path

app = Flask(__name__)
api = Api(
    app,
    version='1.0',
    title='File Reader API',
    description='A simple API to read file contents and list files',
    doc='/swagger'
)

# Define the namespace
ns = api.namespace('files', description='File operations')

# Define the response models
file_list_response = api.model('FileListResponse', {
    'files': fields.List(fields.String, description='List of file names'),
    'status': fields.String(description='Status of the operation')
})

file_content_response = api.model('FileContentResponse', {
    'content': fields.String(description='Content of the file', default=''),
    'filename': fields.String(description='Name of the file', default=''),
    'status': fields.String(description='Status of the operation', default='')
})

# Add cleanup configuration
DIFF_CLEANUP_THRESHOLD = 24 * 60 * 60  # 24 hours in seconds
DIFF_CLEANUP_INTERVAL = 60 * 60  # 1 hour in seconds

def cleanup_old_diff_files():
    """Clean up diff files older than DIFF_CLEANUP_THRESHOLD"""
    while True:
        try:
            diff_dir = Path('diff')
            if diff_dir.exists():
                current_time = time.time()
                for file in diff_dir.glob('diff_*.html'):
                    if current_time - file.stat().st_mtime > DIFF_CLEANUP_THRESHOLD:
                        try:
                            file.unlink()
                        except Exception as e:
                            print(f"Error deleting old diff file {file}: {e}")
        except Exception as e:
            print(f"Error in cleanup thread: {e}")
        time.sleep(DIFF_CLEANUP_INTERVAL)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_diff_files, daemon=True)
cleanup_thread.start()

@ns.route('/list')
class FileLister(Resource):
    @ns.doc('list_files',            responses={
                200: 'Success',
                400: 'Invalid folder path',
                404: 'Folder not found'
            })
    def get(self):
        """List all files in a specified folder"""
        folder_path = 'files'
        try:
            if not os.path.exists(folder_path):
                return jsonify({'files': [], 'status': 'Error: Folder not found'}), 404
                
            if not os.path.isdir(folder_path):
                return jsonify({'files': [], 'status': 'Error: Path is not a folder'}), 400
                
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            print(files)
            return jsonify({
                'files': files,
                'status': 'Success'
            })
        except Exception as e:
            return jsonify({'files': [], 'status': f'Error: {str(e)}'}), 400

@ns.route('/read')
class FileReader(Resource):
    @ns.doc('read_file',
            params={'filename': 'Name of the file to read'},
            responses={
                200: 'Success',
                400: 'Invalid file name',
                404: 'File not found'
            })
    def get(self):
        """Read the content of a file"""
        filename = request.args.get('filename', '')
        
        if not filename:
            return jsonify({'content': '', 'filename': '', 'status': 'Error: No file name provided'}), 400
            
        try:
            filepath = os.path.join('files', filename)
            if not os.path.exists(filepath):
                return jsonify({'content': '', 'filename': filename, 'status': 'Error: File not found'}), 404
                
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read() or ''  # Ensure empty string if read() returns None or empty
                    return jsonify({
                        'content': content,
                        'filename': filename,
                        'status': 'Success'
                    })
            except UnicodeDecodeError:
                # Try reading with a different encoding if UTF-8 fails
                with open(filepath, 'r', encoding='latin-1') as file:
                    content = file.read() or ''  # Ensure empty string if read() returns None or empty
                    return jsonify({
                        'content': content,
                        'filename': filename,
                        'status': 'Success'
                    })
        except Exception as e:
            return jsonify({'content': '', 'filename': filename, 'status': f'Error: {str(e)}'}), 400

@ns.route('/compare')
class FileComparer(Resource):
    @ns.doc('compare_files',
            params={
                'file1_content': 'Content of the first file (optional)',
                'file2_content': 'Content of the second file (optional)'
            },
            responses={
                200: 'Success',
                400: 'Invalid input',
                404: 'File not found'
            })
    def get(self):
        """Compare the content of two files or provided content"""
        file1_content = request.args.get('file1_content', '')
        file2_content = request.args.get('file2_content', '')
                
        try:
            # Escape special characters in the content
            file1_content = escape(file1_content)
            file2_content = escape(file2_content)
            
            # If content is provided directly, use it
            if file1_content and file2_content:
                file1_lines = file1_content.splitlines(True)
                file2_lines = file2_content.splitlines(True)
            
            # Generate diff
            diff = list(difflib.unified_diff(
                file1_lines,
                file2_lines,
                lineterm=''
            ))

            # Process diff into original and modified lines
            original_lines = []
            modified_lines = []
            original_line_num = 1
            modified_line_num = 1

            for line in diff:
                if line.startswith('@'):
                    # Parse the line numbers from the diff header
                    match = re.search(r'@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@', line)
                    if match:
                        original_line_num = int(match.group(1))
                        modified_line_num = int(match.group(3))
                        original_lines.append({
                            'type': 'info',
                            'number': '',
                            'content': line
                        })
                        modified_lines.append({
                            'type': 'info',
                            'number': '',
                            'content': line
                        })
                elif line.startswith('-'):
                    original_lines.append({
                        'type': 'remove',
                        'number': original_line_num,
                        'content': line[1:]
                    })
                    original_line_num += 1
                elif line.startswith('+'):
                    modified_lines.append({
                        'type': 'add',
                        'number': modified_line_num,
                        'content': line[1:]
                    })
                    modified_line_num += 1
                else:
                    if not line.startswith('\\'):
                        original_lines.append({
                            'type': 'context',
                            'number': original_line_num,
                            'content': line
                        })
                        modified_lines.append({
                            'type': 'context',
                            'number': modified_line_num,
                            'content': line
                        })
                        original_line_num += 1
                        modified_line_num += 1
            
            # Create diff directory if it doesn't exist
            diff_dir = Path('diff')
            diff_dir.mkdir(exist_ok=True)
            
            # Generate unique filename with timestamp and UUID
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            filename = f'diff_{timestamp}_{unique_id}.html'
            filepath = diff_dir / filename
            
            # Save the diff HTML to file with proper error handling
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(render_template('file_diff.html', 
                        original_lines=original_lines,
                        modified_lines=modified_lines
                    ))
            except Exception as e:
                return jsonify({'status': f'Error saving diff file: {str(e)}'}), 500
            
            # Return the URL to access the diff file
            diff_url = f'/diff/{filename}'
            return jsonify({
                'status': 'Success',
                'diff_url': diff_url
            })
            
        except Exception as e:
            return jsonify({'status': f'Error: {str(e)}'}), 400

@ns.route('/diff/<path:filename>')
class DiffViewer(Resource):
    @ns.doc('view_diff',
            params={'filename': 'Name of the diff file'},
            responses={
                200: 'Success',
                404: 'File not found'
            })
    def get(self, filename):
        """View a diff file"""
        try:
            return send_from_directory('diff/', filename)
        except Exception as e:
            return jsonify({'status': f'Error: {str(e)}'}), 404

if __name__ == '__main__':
    # Create files directory if it doesn't exist
    if not os.path.exists('files'):
        os.makedirs('files')
    app.run(debug=False,host='0.0.0.0',port=5000)
