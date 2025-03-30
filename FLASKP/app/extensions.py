from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache  
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
cache = Cache()
migrate = Migrate()

# Initialize login manager
@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))