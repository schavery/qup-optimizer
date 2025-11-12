#!/usr/bin/env python3
# app.py
"""Flask application for Qup skill tree optimizer web interface"""
from flask import Flask, send_from_directory
from flask_cors import CORS
import os

from api.routes import api


def create_app():
    """Application factory"""
    app = Flask(__name__, static_folder='frontend/dist', static_url_path='')

    # Enable CORS for development
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register API blueprint
    app.register_blueprint(api, url_prefix='/api')

    # Serve frontend
    @app.route('/')
    def serve_frontend():
        frontend_dir = os.path.join(app.root_path, 'frontend', 'dist')
        if os.path.exists(frontend_dir):
            return send_from_directory(frontend_dir, 'index.html')
        else:
            return """
            <html>
            <head><title>Qup Optimizer</title></head>
            <body>
                <h1>Qup Skill Tree Optimizer API</h1>
                <p>Frontend not built yet. Build the Vue frontend with:</p>
                <pre>cd frontend && npm install && npm run build</pre>
                <p>API available at:</p>
                <ul>
                    <li><a href="/api/health">/api/health</a></li>
                    <li><a href="/api/nodes">/api/nodes</a></li>
                    <li>/api/evaluate (POST)</li>
                    <li>/api/generate-layouts (POST)</li>
                    <li>/api/generate-upgrades (POST)</li>
                    <li><a href="/api/outcomes">/api/outcomes</a></li>
                </ul>
            </body>
            </html>
            """

    # Catch-all route for SPA routing
    @app.route('/<path:path>')
    def serve_spa(path):
        frontend_dir = os.path.join(app.root_path, 'frontend', 'dist')
        if os.path.exists(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        elif os.path.exists(frontend_dir):
            return send_from_directory(frontend_dir, 'index.html')
        return "File not found", 404

    return app


if __name__ == '__main__':
    app = create_app()
    port = 5001
    print("Starting Qup Optimizer server...")
    print(f"API available at: http://localhost:{port}/api")
    print(f"Frontend at: http://localhost:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)
