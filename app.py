import json
import uuid
import urllib
import numpy as np
import pandas as pd
import pymysql
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, UserProfile, Place, BookingDetails

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
def home():
    return render_template('home.html')

@app.route('/index')
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
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash("Email already exists! Please use another email.", "danger")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        user_id = str(uuid.uuid4())

        new_user = User(user_id=user_id, name=name, email=email,
                        password_hash=hashed_password)
        new_user_profile = UserProfile(profile_id=str(uuid.uuid4(
        )), user_id=user_id, age=int(age), gender=gender)

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
            session['email'] = user.email
            session['name'] = user.name
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
    unique_countries.sort()
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
        
        recommendations=filtered_places.to_dict(orient="records")
        # Store recommended places in the database
        for place in recommendations:
            existing_place = Place.query.filter_by(place_name=place['name']).first()
            if not existing_place:
                new_place = Place(
                    place_id=str(uuid.uuid4()),
                    user_id=user_id,
                    place_name=place['name'],
                    cost=place['cost'],
                    region=place['country'],
                    latitude=place['latitude'],
                    longitude=place['longitude']
                )
                db.session.add(new_place)
                db.session.commit()

        return render_template("result.html", recommendations=recommendations, name=session['name'])
    except Exception as e:
        print(e)
        return render_template("result.html", error=str(e))


@app.route('/book_place', methods=['POST'])
def book_place():
    try:
        place_data = request.get_json()  # Get place details from frontend
        session['selected_place'] = place_data  # Store data in session
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/booking_page')
def booking_page():
    if 'selected_place' not in session:
        return redirect(url_for('index'))  # Redirect if no place selected
    cost = session['selected_place']['cost']
    place_name = session['selected_place']['place_name']
    return render_template('booking.html', place_name=place_name, cost=cost)


@app.route('/book_place_database', methods=['POST'])
def book_place_database():
    userAccountObj = User.query.filter_by(email=session['email']).first()
    placeObj = Place.query.filter_by(place_name=request.form.get('place_name')).first()
    bookingObj = BookingDetails(
        booking_id = str(uuid.uuid4()),
        user_id = userAccountObj.user_id,
        place_id = placeObj.place_id,
        check_in = request.form.get('check_in'),
        number_persons = request.form.get('number_persons'),
        total_cost = request.form.get('total_cost')
    )
    db.session.add(bookingObj)
    db.session.commit()
    flash("Place booked successfully!", "success")
    return redirect(url_for('booking_details'))

@app.route('/booking_details', methods=['GET'])
def booking_details():
    if 'user_id' not in session:
        return redirect(url_for('index'))  # Redirect if no place selected
    bookingObj = BookingDetails.query.filter_by(user_id=session['user_id']).first()
    if bookingObj:
        userObj = User.query.filter_by(user_id=bookingObj.user_id).first()
        placeObj = Place.query.filter_by(place_id=bookingObj.place_id).first()
        name = userObj.name
        place_name = placeObj.place_name
        check_in = bookingObj.check_in
        number_persons = bookingObj.number_persons
        total_cost = bookingObj.total_cost
        return render_template('bookingDetails.html', name=name, place_name=place_name, check_in=check_in, number_persons=number_persons, total_cost=total_cost)
    else:
        return render_template('bookingDetails.html', name="")

@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    if 'user_id' not in session:
        return redirect(url_for('index'))  # Redirect if no place selected
    BookingDetails.query.filter_by(user_id=session['user_id']).delete()
    db.session.commit()  # Commit the changes
    flash("Place booking cancelled successfully!", "success")
    return render_template('bookingDetails.html', name="")


if __name__ == '__main__':
    app.run(debug=True)
