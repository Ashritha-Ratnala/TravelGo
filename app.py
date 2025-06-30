from flask import Flask, render_template, request, redirect, session, flash, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os
import boto3

# Flask App Setup
app = Flask(__name__)
app.secret_key = 'e0d15ae2faa18025f4e2a0c7dc5a7b8a830791cc83ad7538667ce14ca2ad8bc0'

# MongoDB Atlas Setup (your real password included here)
client = MongoClient("mongodb+srv://aasritharatnala05:uhS3SbJlbEKFHOJp@cluster0.pmzcrc1.mongodb.net/")
db = client['Travelgo']
users_collection = db['users']
bookings_collection = db['bookings']

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # IMPORTANT: Change this to a strong, random key in production!


# AWS Setup using IAM Role
REGION = 'us-east-1'  # Replace with your actual AWS region
dynamodb = boto3.resource('dynamodb', region_name=REGION)
sns_client = boto3.client('sns', region_name=REGION)


users_table = dynamodb.Table('travelgo_users')
trains_table = dynamodb.Table('trains') # Note: This table is declared but not used in the provided routes.
bookings_table = dynamodb.Table('bookings')


SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:324037304857:TravelGoapplication:149f125c-a946-4513-af12-3928ca7aec77'  

@app.route('/')
def home():
    return render_template('index.html', logged_in='user' in session)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        if users_collection.find_one({"email": email}):
            return render_template('register.html', message="User already exists.")
        
        user_data = {
            "email": email,
            "name": request.form['name'],
            "password": generate_password_hash(request.form['password']),
            "logins": 0
        }
        
        users_collection.insert_one(user_data)
        print(f"[✔] Registered new user: {email}")  # ✅ Log to terminal
        
        flash("Registration successful! Please login.", "success")
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_collection.find_one({"email": email})
        if user and check_password_hash(user['password'], password):
            session['user'] = email
            session['user_name'] = user['name']
            users_collection.update_one({"email": email}, {"$inc": {"logins": 1}})
            flash("Login successful! Welcome back.", "success")
            return redirect('/dashboard')
        flash("Invalid email or password. Please try again.", "error")
        return redirect('/login')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    email = session['user']
    bookings = list(bookings_collection.find({'user_email': email}))
    for b in bookings:
        b['_id'] = str(b['_id'])
    return render_template('dashboard.html', bookings=bookings)


@app.route('/cancel', methods=['POST'])
def cancel_booking():
    if 'user' not in session:
        return redirect('/login')
    
    booking_id = request.form.get('booking_id')
    user_email = session['user']
    
    try:
        # Delete the booking from database
        result = bookings_collection.delete_one({
            '_id': ObjectId(booking_id),
            'user_email': user_email
        })
        
        if result.deleted_count > 0:
            flash("Booking cancelled successfully!", "success")
        else:
            flash("Booking not found or already cancelled.", "error")
    except Exception as e:
        flash("Error cancelling booking. Please try again.", "error")
    
    return redirect('/dashboard')

# Booking routes
@app.route('/bus')
def bus_booking():
    if 'user' not in session:
        flash("Please login to book tickets.", "error")
        return redirect('/login')
    return render_template('bus.html')

@app.route('/train')
def train_booking():
    if 'user' not in session:
        flash("Please login to book tickets.", "error")
        return redirect('/login')
    return render_template('train.html')

@app.route('/flight')
def flight_booking():
    if 'user' not in session:
        flash("Please login to book tickets.", "error")
        return redirect('/login')
    return render_template('flight.html')

@app.route('/hotel')
def hotel_booking():
    if 'user' not in session:
        flash("Please login to book tickets.", "error")
        return redirect('/login')
    return render_template('hotel.html')

# Sample booking creation routes (you can expand these)
@app.route('/api/book_bus', methods=['POST'])
def api_book_bus():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    booking_data = {
        'user_email': session['user'],
        'type': 'Bus',
        'from': data.get('from'),
        'to': data.get('to'),
        'date': data.get('date'),
        'seat': data.get('seat'),
        'bus_name': data.get('busName'),
        'price': data.get('price'),
        'status': data.get('status', 'Confirmed')
    }

    bookings_collection.insert_one(booking_data)
    return jsonify({'message': 'Bus booked successfully!'}), 200

@app.route('/api/book_train', methods=['POST'])
def api_book_train():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()

    booking_data = {
        'user_email': session['user'],
        'type': 'Train',
        'from': data.get('from'),
        'to': data.get('to'),
        'date': data.get('date'),
        'seat': data.get('seat'),
        'train_name': data.get('trainName'),
        'train_number': data.get('trainNumber'),
        'price': data.get('price'),
        'status': 'Confirmed'
    }

    try:
        bookings_collection.insert_one(booking_data)
        return jsonify({'message': 'Train booked successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/book_flight', methods=['POST'])
def book_flight():
    if 'user' not in session:
        return redirect('/login')
    
    booking_data = {
        'user_email': session['user'],
        'type': 'Flight',
        'from': request.form.get('from'),
        'to': request.form.get('to'),
        'date': request.form.get('date'),
        'seat': request.form.get('seat'),
        'price': request.form.get('price'),
        'status': 'Confirmed'
    }
    
    bookings_collection.insert_one(booking_data)
    flash("Flight ticket booked successfully!", "success")
    return redirect('/dashboard')

@app.route('/api/book_hotel', methods=['POST'])
def api_book_hotel():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    booking_data = {
        'user_email': session['user'],
        'type': 'Hotel',
        'hotel_name': data.get('hotelName'),
        'location': data.get('location'),
        'checkin': data.get('checkIn'),
        'checkout': data.get('checkOut'),
        'guests': data.get('guests'),
        'room_type': data.get('roomType'),
        'price': data.get('price'),
        'status': 'Confirmed'
    }

    bookings_collection.insert_one(booking_data)
    return jsonify({"message": "Hotel booked and saved!"}), 200

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
