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
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('profile', uselist=False, cascade="all, delete"))

class Place(db.Model):
    place_id = db.Column(db.String(36), primary_key=True, unique=True, nullable=False, default=str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    place_name = db.Column(db.String(255), nullable=False)
    region = db.Column(db.String(255), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

class BookingDetails(db.Model):
    booking_id = db.Column(db.String(36), primary_key=True, unique=True, nullable=False, default=str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    place_id = db.Column(db.String(36), db.ForeignKey('place.place_id'), nullable=False)
    check_in = db.Column(db.String(255), nullable=False)
    number_persons = db.Column(db.Integer, nullable=False)
    total_cost = db.Column(db.String(255), nullable=False)
    