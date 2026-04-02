from flask import Flask, render_template, request
import json
import os
import uuid
import datetime

app = Flask(__name__)

rooms = {
    'standard': {'name': 'Standard', 'price': 100},
    'deluxe': {'name': 'Deluxe', 'price': 150},
    'suite': {'name': 'Suite', 'price': 200}
}

def is_available(room_type, checkin, checkout):
    if os.path.exists('bookings.json'):
        with open('bookings.json') as f:
            bookings = json.load(f)
    else:
        bookings = []
    for b in bookings:
        if b['room_type'] == room_type:
            b_checkin = datetime.date.fromisoformat(b['checkin'])
            b_checkout = datetime.date.fromisoformat(b['checkout'])
            if not (checkout <= b_checkin or checkin >= b_checkout):
                return False
    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    checkin = request.form['checkin']
    checkout = request.form['checkout']
    checkin_date = datetime.date.fromisoformat(checkin)
    checkout_date = datetime.date.fromisoformat(checkout)
    if checkin_date >= checkout_date:
        return "Invalid dates"
    available = []
    for rt, info in rooms.items():
        if is_available(rt, checkin_date, checkout_date):
            available.append({'type': rt, **info})
    return render_template('results.html', available=available, checkin=checkin, checkout=checkout)

@app.route('/book/<room_type>')
def book(room_type):
    checkin = request.args['checkin']
    checkout = request.args['checkout']
    if room_type not in rooms:
        return "Invalid room"
    return render_template('book.html', room=rooms[room_type], room_type=room_type, checkin=checkin, checkout=checkout)

@app.route('/confirm', methods=['POST'])
def confirm():
    room_type = request.form['room_type']
    checkin = request.form['checkin']
    checkout = request.form['checkout']
    name = request.form['name']
    email = request.form['email']
    checkin_date = datetime.date.fromisoformat(checkin)
    checkout_date = datetime.date.fromisoformat(checkout)
    if not is_available(room_type, checkin_date, checkout_date):
        return "Room not available"
    ref = str(uuid.uuid4())
    booking = {
        'ref': ref,
        'room_type': room_type,
        'checkin': checkin,
        'checkout': checkout,
        'name': name,
        'email': email
    }
    if os.path.exists('bookings.json'):
        with open('bookings.json') as f:
            bookings = json.load(f)
    else:
        bookings = []
    bookings.append(booking)
    with open('bookings.json', 'w') as f:
        json.dump(bookings, f)
    nights = (checkout_date - checkin_date).days
    total = rooms[room_type]['price'] * nights
    return render_template('confirm.html', booking=booking, total=total, rooms=rooms)

@app.route('/cancel', methods=['GET', 'POST'])
def cancel():
    if request.method == 'POST':
        ref = request.form['ref']
        if os.path.exists('bookings.json'):
            with open('bookings.json') as f:
                bookings = json.load(f)
        else:
            bookings = []
        for i, b in enumerate(bookings):
            if b['ref'] == ref:
                del bookings[i]
                with open('bookings.json', 'w') as f:
                    json.dump(bookings, f)
                return render_template('cancel.html', success=True, booking=b, rooms=rooms)
        return render_template('cancel.html', success=False)
    return render_template('cancel.html')

if __name__ == '__main__':
    app.run(debug=True)