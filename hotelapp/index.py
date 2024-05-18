from __init__ import app, login_manager, Message, mail
from flask import render_template, request, session, jsonify, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from admin import admin
import dao
import utils
from decorators import loggedin, staffonly
from datetime import datetime, timedelta
from sqlalchemy import func


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/staff/')
@staffonly
@login_required
def staff_index():
    bookings = dao.get_bookings()
    return render_template('staff/index.html', bookings=bookings, title="Booking")


@app.route('/staff/bookings/<booking_id>')
@staffonly
@login_required
def staff_booking_detail(booking_id):
    booking = dao.get_booking_by_id(booking_id)
    print(booking.get_guests())
    return render_template('staff/detail.html', booking=booking, title="Booking")


@app.route('/staff/booking')
@staffonly
@login_required
def staff_booking():
    check_in = request.args.get('check-in', datetime.today().date().strftime(
        '%Y-%m-%d'))
    check_out = request.args.get(
        'check-out', (datetime.today().date() + timedelta(days=1)).strftime('%Y-%m-%d'))
    booking_id = request.args.get('booking-id', None)
    template = 'staff/booking/booking.html'

    cart = session.get('cart')

    if cart:
        if check_in != cart['check_in'] or check_out != cart['check_out']:
            session.pop('cart', default=None)

    if booking_id:
        cart = {
            "check_in": check_in,
            "check_out": check_out,
        }

        booking = dao.get_booking_by_id(booking_id)
        cart['items'] = [{"room": room.id, "room_type": room.get_room_type().id}
                         for room in booking.rooms]
        cart['guests'] = [{"name": guest.get_guest().name, "identity": guest.get_guest(
        ).identity_num, "is_vietnamese": guest.get_guest().is_vietnamese, "room": guest.room_id} for guest in booking.guests]
        cart['booking_id'] = booking_id
        session['cart'] = cart
        template = 'staff/booking/reservation.html'

    if request.referrer.__contains__("reservations"):
        template = 'staff/booking/reservation.html'

    room_types = dao.get_room_types()
    return render_template(template, rooms=room_types, check_in=check_in, check_out=check_out)


@app.route('/staff/booking-checkout')
@staffonly
@login_required
def staff_booking_checkout():
    rooms = dao.get_rooms()
    room_types = dao.get_room_types()

    template = 'staff/form/booking-checkout.html'
    return render_template(template, rooms=rooms, room_types=room_types)


@app.route('/staff/reservation-checkout')
@staffonly
@login_required
def staff_reservation_checkout():
    rooms = dao.get_rooms()
    room_types = dao.get_room_types()

    template = 'staff/form/reservation-checkout.html'
    return render_template(template, rooms=rooms, room_types=room_types)


@app.route('/staff/reservations')
@staffonly
@login_required
def staff_reservations():
    reservations = dao.get_reservations()
    return render_template('staff/reservations.html', reservations=reservations, title="Reservation")


@app.route('/staff/reservations/<reservation_id>')
@staffonly
@login_required
def staff_reservation_detail(reservation_id):
    reservation = dao.get_reservation_by_id(reservation_id)
    return render_template('staff/detail.html', booking=reservation, title="Reservation")


@app.route('/book', methods=['post'])
def book():
    if request.method == "POST":
        booker = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "notes": request.form.get("notes"),
        }
        try:
            booking = dao.add_booking(booker, session.get('cart'))
            msg = Message('WHATS UP MAN', sender='pthinh.lama@gmail.com',
                          recipients=[booking.email])
            msg.html = render_template(
                "booking-successful.html", booking=booking)
            mail.send(msg)
        except Exception as ex:
            print(ex)
            return jsonify({'status': 500})
        else:
            del session['cart']

    return render_template('index.html')


@app.route('/reservate', methods=['post'])
def reservate():
    if request.method == "POST":
        try:
            dao.add_reservation(session.get('cart'))
        except Exception as ex:
            print(ex)
            return jsonify({'status': 500})
        else:
            del session['cart']

    return render_template('index.html')


@app.route('/booking')
def booking():
    check_in = request.args.get('check-in', datetime.today().date().strftime(
        '%Y-%m-%d'))
    check_out = request.args.get(
        'check-out', (datetime.today().date() + timedelta(days=1)).strftime('%Y-%m-%d'))
    cart = session.get('cart')

    if cart:
        if check_in != cart['check_in'] or check_out != cart['check_out']:
            session.pop('cart', default=None)

    rooms = dao.get_room_types()
    return render_template('booking.html', rooms=rooms, check_in=check_in, check_out=check_out)


@app.route('/checkout')
def checkout():
    rooms = dao.get_rooms()
    room_types = dao.get_room_types()
    return render_template('checkout.html', rooms=rooms, room_types=room_types)


@app.route('/login', methods=['get', 'post'])
@loggedin
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = dao.auth_user(email=email, password=password)
        if user:
            login_user(user)
            next = request.args.get('next')
            return redirect(next if next else '/')
    return render_template('login.html')


@app.route('/logout', methods=['get'])
def logout():
    logout_user()
    return redirect('/login')


@app.route('/profile')
def profile():
    bookings = dao.get_bookings_by_phone("678901234")
    return render_template('profile.html', bookings=bookings)


@app.route('/register', methods=['post'])
def register():
    if request.method == "POST":
        phone = request.form.get("phone")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        user = dao.auth_user(email=email, password=password)
        if user:
            login_user(user)
            return redirect('/')
        dao.add_user(email=email, password=password,
                     first_name=first_name, last_name=last_name, phone=phone)

    return render_template('login.html')


@app.route('/api/room_types', methods=['get'])
def get_room_types():
    rooms = dao.get_room_types()
    return {'data': [utils.room_type_serializer(room) for room in rooms]}


@app.route('/api/room_types/<room_id>', methods=['get'])
def get_room_type(room_id):
    room = dao.get_room_type_by_id(room_id)
    return jsonify({'data': utils.room_type_serializer(room)})


@app.route('/api/rooms', methods=['get'])
def get_rooms():
    rooms = dao.get_rooms()
    return {'data': [utils.room_serializer(room) for room in rooms]}


@app.route('/api/cart', methods=['get'])
def get_cart():
    cart = session.get('cart')
    if not cart:
        return jsonify({})

    return jsonify(get_cart_total(cart))


@app.route('/api/cart', methods=['post'])
def add_to_cart():
    cart = session.get('cart')
    if not cart:
        cart = {
            "check_in": request.json.get("checkIn"),
            "check_out": request.json.get("checkOut"),
            'items': []
        }

    id = str(request.json.get('id'))

    room_type = dao.get_room_type_by_id(id)
    rooms = room_type.check_available(cart['check_in'], cart['check_out'])

    index = 0
    while (index < len(rooms) and any(item['room'] == rooms[index].id for item in cart['items'])):
        index += 1

    if index < len(rooms):
        cart['items'].append(
            {"room": rooms[index].id, "room_type": room_type.id})
    session['cart'] = cart

    return jsonify(get_cart_total(cart))


@app.route('/api/cart/<room_id>', methods=['delete'])
def delete_cart_item(room_id):
    cart = session.get('cart')

    if cart:
        cart['items'] = [item for item in cart['items']
                         if item['room'] != int(room_id)]
        session['cart'] = cart

    return jsonify(get_cart_total(cart))


@app.route('/api/cart/<room_id>', methods=['put'])
def update_cart_item(room_id):
    cart = session.get('cart')
    if cart:
        quantity = int(request.json.get("quantity", 0))
        if (quantity == 0):
            [item.update({'quantity': 1})
             for item in cart['items'] if item['id'] == room_id]
        else:
            room = dao.get_room_type_by_id(room_id)
            [item.update({'quantity': quantity})
             for item in cart['items'] if item['id'] == room_id and
             quantity <= len(room.check_available(cart['check_in'], cart['check_out']))]

        session['cart'] = cart

    return jsonify(get_cart_total(cart))


def get_cart_total(cart):
    total_amount = 0

    if cart:
        for item in cart['items']:
            room_type = dao.get_room_type_by_id(item['room_type'])
            total_amount += room_type.price

    return {
        'items': cart['items'],
        'total_amount': total_amount,
        'total_quantity': len(cart['items']),
    }


@app.route('/api/guests', methods=['post'])
def add_guest_info():
    cart = session.get('cart')
    guests = cart.get('guests')
    if not guests:
        guests = []

    name = str(request.json.get('name'))
    identity = str(request.json.get('identity'))
    room = str(request.json.get("room_id"))
    is_vietnamese = request.json.get("is_vietnamese")

    if any(item['identity'] == identity for item in guests):
        [item.update({'name': name, 'room': room, "is_vietnamese": is_vietnamese})
         for item in guests
         if item['identity'] == identity]
    else:
        guests.append({"name": name, "identity": identity,
                      "room": room, "is_vietnamese": is_vietnamese})

    cart['guests'] = guests
    print(cart)
    session['cart'] = cart
    return jsonify({})


@app.route('/api/guests', methods=['get'])
def get_guests_info():
    cart = session.get('cart')
    guests = cart.get('guests')

    if guests:
        return jsonify(guests)
    return jsonify({})


@app.route('/api/guests/<guest_id>', methods=['delete'])
def remove_guest_info(guest_id):
    cart = session.get('cart')
    guests = cart.get('guests')

    if guests:
        cart['guests'] = [item for item in guests if item['identity'] != guest_id]

    session['cart'] = cart
    return jsonify({})


@app.route('/api/invoice/set-status', methods=['patch'])
def set_invoice_status():
    invoice_id = request.json.get('invoice_id', None)
    invoice_type = str(request.json.get('invoice_type', None))
    invoice_status = str(request.json.get('invoice_status', None))
    dao.set_invoice_status(
        invoice_id=invoice_id, invoice_type=invoice_type, status=invoice_status)

    return jsonify({"msg": "ok"})


@login_manager.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route("/admin-login", methods=['post'])
def process_admin_login():
    email = request.form.get('email')
    password = request.form.get('password')
    u = dao.auth_user(email=email, password=password)
    if u:
        login_user(user=u)

    return redirect('/admin')


if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
