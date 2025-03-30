from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')
    profile_image = db.Column(db.String(200))
    
    # Relationships using string references
    favorites = db.relationship('Quote', secondary='user_favorites', backref='favorited_by')
    quotes = db.relationship('Quote', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_profile_image(self):
        if self.profile_image:
            return f'/uploads/{self.profile_image}'
        return '/static/images/default-avatar.png'

user_favorites = db.Table('user_favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('quote_id', db.Integer, db.ForeignKey('quote.id'))
)