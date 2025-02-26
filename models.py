from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
import uuid
from datetime import datetime

db = SQLAlchemy()

# User Model
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

# User Profile Model
class UserProfile(db.Model):
    __tablename__ = 'user_profile'
    profile_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    age = db.Column(db.Integer, nullable=False)  # Removed check_constraint
    gender = db.Column(Enum('Male', 'Female', 'Other'), nullable=False)
    preferences = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('profile', uselist=False, cascade="all, delete"))

# Search History Model
class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    search_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    search_query = db.Column(db.Text, nullable=False)
    search_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('search_history', cascade="all, delete"))

# AI Recommendation Model
class AIRecommendation(db.Model):
    __tablename__ = 'ai_recommendations'
    recommendation_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    recommendation_type = db.Column(Enum('Place', 'Itinerary'), nullable=False)
    recommendation_data = db.Column(db.JSON, nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)  # Removed check_constraint
    generated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('recommendations', cascade="all, delete"))
