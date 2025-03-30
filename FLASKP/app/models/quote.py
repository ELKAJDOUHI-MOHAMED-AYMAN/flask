from app.extensions import db
from datetime import datetime

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100))  # This could be either free text or relation
    approved = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    average_rating = db.Column(db.Float, default=0.0)
    ratings = db.relationship('Rating', backref='quote', lazy=True)


    def serialize(self):
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author,
            'approved': self.approved,
            'average_rating': self.average_rating
        }

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'))
    value = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)