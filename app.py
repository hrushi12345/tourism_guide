import json
import uuid
import urllib
import numpy as np
import pandas as pd
import pymysql
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, UserProfile, SearchHistory, AIRecommendation

pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.secret_key = "!@#$%QWER^&*()POIYTREWQ"

# Load config
with open('config.json', 'r') as file:
    data = json.load(file)

dbUserName = urllib.parse.quote_plus(data['username'])
dbPassword = urllib.parse.quote_plus(data['password'])
dbHost = data['host']
dbName = data['database']
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{dbUserName}:{dbPassword}@{dbHost}/{dbName}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
places_df = pd.read_csv("dataset_model_training/places_dataset_real.csv")


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        age = request.form['age']
        gender = request.form['gender']
        preferences = request.form['preferences']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash("Email already exists! Please use another email.", "danger")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        user_id = str(uuid.uuid4())

        new_user = User(user_id=user_id, name=name, email=email,
                        password_hash=hashed_password)
        new_user_profile = UserProfile(profile_id=str(uuid.uuid4(
        )), user_id=user_id, age=int(age), gender=gender, preferences=preferences)

        db.session.add(new_user)
        db.session.add(new_user_profile)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.user_id
            return redirect(url_for('index'))
        flash("Invalid email or password.", "danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))


@app.route('/api/countries', methods=['GET'])
def get_countries():
    search_term = request.args.get('term', '').strip().lower()
    unique_countries = places_df['country'].dropna().unique()
    filtered_countries = [c for c in unique_countries if search_term in c.lower(
    )] if search_term else list(unique_countries)
    return jsonify(filtered_countries)


@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    country = request.args.get("country")
    if not country:
        return render_template("result.html", error="Country parameter is missing")

    try:
        filtered_places = places_df[places_df["country"] == country].sort_values(
            by="rating", ascending=False)
        top_recommendations = filtered_places.head(3).to_dict(orient="records")

        # Log search history
        search_entry = SearchHistory(search_id=str(
            uuid.uuid4()), user_id=user_id, search_query=country)
        db.session.add(search_entry)

        # Store AI Recommendations
        ai_recommendation = AIRecommendation(
            recommendation_id=str(uuid.uuid4()),
            user_id=user_id,
            recommendation_type="Place",
            recommendation_data=top_recommendations,
            confidence_score=np.random.uniform(0.75, 0.95)
        )
        db.session.add(ai_recommendation)

        db.session.commit()

        return render_template("result.html", recommendations=filtered_places.to_dict(orient="records"))

    except Exception as e:
        return render_template("result.html", error=str(e))


if __name__ == '__main__':
    app.run(debug=True)
