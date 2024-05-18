import hashlib
from __init__ import db
from flask_login import current_user
from models import *
from sqlalchemy import extract, func
from datetime import datetime


def get_room_types():
    query = RoomType.query
    return query.all()


def get_room_type_by_id(id):
    return RoomType.query.get(id)


def get_user_by_id(id):
    return User.query.get(id)


def get_rooms():
    return Room.query.all()


def get_room_by_id(id):
    return Room.query.get(id)


def get_guests():
    return Guest.query.all()


def get_guest_by_id(id):
    return Guest.query.get(id)


def get_amenity_types():
    return AmenityType.query.all()


def get_bookings():
    return Booking.query.all()


def get_bookings_by_phone(phone):
    return Booking.query.filter(Booking.phone.__eq__(phone)).all()


def get_booking_by_id(id):
    return Booking.query.get(id)


def get_reservations():
    return Reservation.query.all()


def get_reservation_by_id(reservation_id):
    return Reservation.query.get(reservation_id)


def set_invoice_status(invoice_id, invoice_type, status):
    invoice_status = InvoiceStatus[status]
    if invoice_type == "Booking":
        booking = Booking.query.get(invoice_id)
        if booking.invoice.status != InvoiceStatus.PAID:
            booking.set_invoice_status(invoice_status)
    else:
        reservation = Reservation.query.get(invoice_id)
        if reservation.invoice.status != InvoiceStatus.PAID:
            reservation.set_invoice_status(invoice_status)


def auth_user(email, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(User.email.__eq__(email.strip()),
                             User.password.__eq__(password)).first()


def is_customer():
    return current_user.role.__eq__(UserRole.CUSTOMER)


def add_user(email, password, first_name, last_name, phone):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    user = User(email=email, password=password,
                first_name=first_name, last_name=last_name, phone=phone)
    db.session.add(user)


def add_booking(booker, cart):
    if booker and cart['guests'] and cart['items']:
        booking = Booking(
            name=booker['name'], phone=booker['phone'], email=booker['email'], notes=booker['notes'],
            check_out=cart['check_out'], check_in=cart['check_in'])
        db.session.add(booking)

        for guest_data in cart['guests']:
            room = guest_data['room']
            guest = [item for item in get_guests() if guest_data['identity']
                     == item.identity_num]

            if guest:
                guest = guest[0]
            else:
                guest = Guest(
                    name=guest_data['name'], identity_num=guest_data['identity'],
                    is_vietnamese=guest_data['is_vietnamese'])
                db.session.add(guest)
                db.session.commit()

            booking_guest = BookingGuest(
                booking_id=booking.id, guest_id=guest.id, room_id=room)
            db.session.add(booking_guest)

        for room_data in cart['items']:
            room = get_room_by_id(room_data['room'])
            booking.add_room(room=room)

        db.session.commit()
        return booking


def add_reservation(cart):
    if cart['guests'] and cart['items']:
        booking_id = cart["booking_id"]
        reservation = Reservation(
            check_out=cart['check_out'], check_in=cart['check_in'], receptionist=current_user.id, booking=booking_id)

        db.session.add(reservation)

        for guest_data in cart['guests']:
            room = guest_data['room']
            guest = [item for item in get_guests() if guest_data['identity']
                     == item.identity_num]

            if guest:
                guest = guest[0]
            else:
                guest = Guest(
                    name=guest_data['name'], identity_num=guest_data['identity'],
                    is_vietnamese=guest_data['is_vietnamese'])
                db.session.add(guest)
                db.session.commit()

            reservation_guest = ReservationGuest(
                reservation_id=reservation.id, guest_id=guest.id, room_id=room)
            db.session.add(reservation_guest)

        for room_data in cart['items']:
            room = get_room_by_id(room_data['room'])
            reservation.add_room(room=room)

        # create reservation invoice
        reservation.create_invoice(receptionist=current_user.id)

        db.session.commit()
        return reservation


def load_room_detail(room_id):
    # Truy vấn RoomType cùng với danh sách các Amenity có trong đó
    query = (
        db.session.query(RoomType, Amenity,
                         AmenityRoom.quantity)
        .join(AmenityRoom, RoomType.id == AmenityRoom.room)
        .join(Amenity, Amenity.id == AmenityRoom.amenity)
        .filter(RoomType.id == room_id)
        .all()
    )

    # Tạo một từ điển chứa thông tin RoomType và danh sách các Amenity
    room_type_info = {}
    for room_type, amenity, quantity in query:
        if 'room_type' not in room_type_info:
            # Lưu thông tin RoomType
            room_type_info['room_type'] = {
                'id': room_type.id,
                'name': room_type.name,
                'room_size': room_type.room_size,
                'description': room_type.description,
                'adults': room_type.adults,
                'children': room_type.children,
                'price': room_type.price
            }
            # Khởi tạo danh sách Amenities
            room_type_info['amenities'] = []
        # Thêm thông tin của mỗi Amenity vào danh sách Amenities
        room_type_info['amenities'].append({
            'id': amenity.id,
            'name': amenity.name,
            'description': amenity.description,
            'quantity': quantity
        })

    return room_type_info


def revenue_by_month(month=None, year=None):
    current_year = datetime.now().year

    if year is None and month is None:
        # Không có năm và tháng, thống kê theo năm hiện tại
        year = current_year
        filter_criteria = [extract('year', Reservation.check_in) == year]
    elif year is not None and month is None:
        # Có năm, không có tháng -> thống kê theo năm
        filter_criteria = [extract('year', Reservation.check_in) == year]
    elif year is not None and month is not None:
        # Có năm và có tháng -> thống kê theo tháng và năm
        filter_criteria = [
            extract('month', Reservation.check_in) == month,
            extract('year', Reservation.check_in) == year
        ]
    elif year is None and month is not None:
        # Có tháng, không có năm -> thống kê theo tháng của năm hiện tại
        year = current_year
        filter_criteria = [
            extract('month', Reservation.check_in) == month,
            extract('year', Reservation.check_in) == year
        ]

    results = db.session.query(
        RoomType.name.label('room_type'),
        func.count(Reservation.id).label('num_reservations'),
        func.sum(ReservationInvoice.amount).label('total_revenue')
    ).select_from(Reservation).join(
        Reservation.rooms).join(
        RoomType, Room.room_type == RoomType.id).join(
        ReservationInvoice, Reservation.id == ReservationInvoice.reservation
    ).filter(
        *filter_criteria
    ).group_by(RoomType.name).all()

    statistics = []
    for result in results:
        statistics.append({
            'room_type': result.room_type,
            'num_reservations': result.num_reservations,
            'total_revenue': result.total_revenue
        })

    return statistics


def get_num_days_in_month(month, year):  # lấy ngày của tháng
    if month in [4, 6, 9, 11]:
        return 30
    elif month == 2:
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 29
        else:
            return 28
    else:
        return 31


def room_utilization(month=None, year=None):
    current_year = datetime.now().year
    current_month = datetime.now().month

    if year is None and month is None:
        # Không có năm và tháng, thống kê theo năm hiện tại
        year = current_year
        month = current_month
    elif year is not None and month is None:
        # Có năm, không có tháng
        month = None
    elif year is None and month is not None:
        # Có tháng, không có năm
        year = current_year

    if month is not None:
        num_days_in_month = get_num_days_in_month(month, year)
        filter_criteria = [
            extract('month', Reservation.check_in) == month,
            extract('year', Reservation.check_in) == year
        ]
    else:
        num_days_in_month = 365 if (year % 4 == 0 and year % 100 != 0) or (
            year % 400 == 0) else 364
        filter_criteria = [
            extract('year', Reservation.check_in) == year
        ]

    results = db.session.query(
        Room.name,
        func.sum(func.datediff(Reservation.check_out, Reservation.check_in)).label(
            'num_days_reserved')
    ).outerjoin(
        reservation_room, Room.id == reservation_room.c.room_id
    ).outerjoin(
        Reservation, reservation_room.c.reservation_id == Reservation.id
    ).filter(
        *filter_criteria
    ).group_by(Room.name).all()

    room_utilization_data = []
    for result in results:
        utilization_rate = (result.num_days_reserved / num_days_in_month) * 100
        room_utilization_data.append({
            'room_name': result.name,
            'num_days_reserved': result.num_days_reserved,
            'utilization_rate': utilization_rate
        })
    return room_utilization_data


def auth_user(email, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(User.email.__eq__(email.strip()),
                             User.password.__eq__(password)).first()
