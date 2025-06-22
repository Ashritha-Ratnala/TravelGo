from flask import Flask, render_template, request, redirect, url_for, session, flash
import uuid

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Local user store (simulated)
users = {}
bookings = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']

        if email in users:
            flash('User already exists!')
            return redirect(url_for('register'))

        users[email] = {'password': password, 'name': name}
        flash('Registered successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email in users and users[email]['password'] == password:
            session['email'] = email
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))

    user_bookings = [b for b in bookings if b['user_email'] == session['email']]
    return render_template('dashboard.html', bookings=user_bookings)

@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        booking_id = str(uuid.uuid4())
        booking = {
            'booking_id': booking_id,
            'user_email': session['email'],
            'type': request.form['type'],
            'destination': request.form['destination'],
            'date': request.form['date'],
            'status': 'Confirmed'
        }
        bookings.append(booking)
        flash('Booking successful!')
        return redirect(url_for('dashboard'))

    return render_template('booking.html')

# 🟢 NEW: Handle "search" requests
@app.route('/search/<transport_type>')
def search(transport_type):
    return f"<h2>Showing available {transport_type.title()} options...</h2><p>(You can implement filters and results here later.)</p>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
