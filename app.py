"""
Flask web application for the RAG system.
Provides a web interface for document upload and querying.
WITH CONVERSATION HISTORY — original Flask version restored.
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from rag_system import RAGSystem
import io

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = './documents'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print("Initializing RAG system...")
rag_system = RAGSystem()
print("RAG system ready!")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = rag_system.get_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': f'File type not allowed. Supported: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        rag_system.index_single_document(file_path)
        return jsonify({'success': True, 'message': f'File "{filename}" uploaded and indexed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query():
    data = request.json
    if not data or 'question' not in data:
        return jsonify({'success': False, 'error': 'No question provided'}), 400
    question = data['question']
    session_id = data.get('session_id')
    top_k = data.get('top_k', 5)
    use_history = data.get('use_history', True)
    try:
        result = rag_system.query(
            question,
            session_id=session_id,
            top_k=top_k,
            use_history=use_history
        )
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'sources': result.get('sources', []),
            'session_id': result['session_id']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── Conversation endpoints ─────────────────────────────────────────

@app.route('/api/conversations', methods=['GET'])
def list_conversations():
    try:
        conversations = rag_system.list_conversations()
        return jsonify({'success': True, 'conversations': conversations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/conversations/<session_id>', methods=['GET'])
def get_conversation(session_id):
    try:
        conversation = rag_system.get_conversation(session_id)
        if conversation:
            return jsonify({'success': True, 'conversation': conversation})
        return jsonify({'success': False, 'error': 'Conversation not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    try:
        session_id = rag_system.create_session()
        return jsonify({'success': True, 'session_id': session_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/conversations/<session_id>', methods=['DELETE'])
def delete_conversation(session_id):
    try:
        rag_system.delete_conversation(session_id)
        return jsonify({'success': True, 'message': 'Conversation deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/conversations/clear-all', methods=['POST'])
def clear_all_conversations():
    try:
        rag_system.clear_all_conversations()
        return jsonify({'success': True, 'message': 'All conversations cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/conversations/<session_id>/export', methods=['GET'])
def export_conversation(session_id):
    format = request.args.get('format', 'txt')
    try:
        content = rag_system.export_conversation(session_id, format)
        output = io.BytesIO()
        output.write(content.encode('utf-8'))
        output.seek(0)
        filename = f"conversation_{session_id}.{format}"
        return send_file(
            output,
            mimetype='text/plain' if format == 'txt' else 'text/markdown',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── Other endpoints ────────────────────────────────────────────────

@app.route('/api/index-all', methods=['POST'])
def index_all():
    try:
        rag_system.index_documents()
        return jsonify({'success': True, 'message': 'All documents indexed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_index():
    try:
        rag_system.clear_index()
        return jsonify({'success': True, 'message': 'Index cleared successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'success': False, 'error': 'No message provided'}), 400
    try:
        response = rag_system.chat_without_rag(data['message'])
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("RAG System Web Interface")
    print("="*60)
    print("Access at: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=False, host='0.0.0.0', port=7860)