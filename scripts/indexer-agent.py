from flask import Flask, jsonify
from datetime import datetime
import random

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'agent': 'code-indexer-1',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/index')
def index():
    return jsonify({
        'indexed_files': random.randint(1000, 2000),
        'status': 'indexing',
        'languages': ['python', 'javascript', 'solidity'],
        'last_updated': datetime.now().isoformat()
    })

@app.route('/search')
def search():
    return jsonify({
        'results': [
            {'file': 'contract.sol', 'type': 'smart_contract', 'functions': 15},
            {'file': 'api.py', 'type': 'python_module', 'functions': 8},
            {'file': 'frontend.js', 'type': 'javascript', 'functions': 12}
        ],
        'total_results': 3
    })

@app.route('/stats')
def stats():
    return jsonify({
        'total_files': random.randint(800, 1200),
        'total_functions': random.randint(5000, 8000),
        'total_lines': random.randint(50000, 80000)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
