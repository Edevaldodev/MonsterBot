import os

def create_app(test_config=None):
    from flask import Flask
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "local-dev-key-change-me"),
        DATABASE=os.path.join(app.instance_path, "monster_bot.sqlite3"),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    from .database import init_db
    init_db(app)
    from .routes import bp
    app.register_blueprint(bp)
    return app
