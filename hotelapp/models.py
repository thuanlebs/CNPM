from __init__ import db, app
from sqlalchemy import Column, String, Integer, ForeignKey, Float, Date, Boolean, DateTime, Enum, Double, Table, BINARY, Text, event
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship
from enum import Enum as Enumeration
import json
from flask_login import UserMixin
import utils
import hashlib
from random import randint


class UserStatus(Enumeration):
    ACTIVE = 1
    BLACKLISTED = 2
    CANCELED = 3


class UserRole(Enumeration):
    ADMIN = 1
    CUSTOMER = 2
    RECEPTIONIST = 3


class RoomStatus(Enumeration):
    AVAILABLE = 1
    RESERVED = 2
    BEING_SERVICED = 3
    OTHER = 4


class Rating(Enumeration):
    POOR = 1
    FAIR = 2
    GOOD = 3
    VERY_GOOD = 4
    EXCELLENT = 5


class BookingStatus(Enumeration):
    CONFIRMED = 1
    CHECKED_IN = 2
    CHECKED_OUT = 3
    CANCELED = 4


class InvoiceStatus(Enumeration):
    UNPAID = 1
    PAID = 2
    PENDING = 3


class Person(db.Model):
    __abstract__ = True
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), nullable=False)
    address = Column(Text)
    identity_num = Column(String(20), unique=True)


class User(Person, UserMixin):
    first_name = Column(String(50))
    phone = Column(String(11), nullable=False, unique=True)
    email = Column(String(40), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    avatar = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)


class Guest(Person):
    is_vietnamese = Column(Boolean, default=True)

    def __str__(self):
        return self.name


class ServiceStaff(Person):
    pass


class AmenityType(db.Model):
    id = Column(Integer, autoincrement=True,  primary_key=True)
    name = Column(String(50), nullable=False)
    amenities = relationship("Amenity", backref="type")

    def __str__(self):
        return self.name


class Amenity(db.Model):
    id = Column(Integer, autoincrement=True,  primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    amenity_type = Column(Integer, ForeignKey(AmenityType.id))

    def __str__(self):
        return self.name


class RoomType(db.Model):
    id = Column(Integer, autoincrement=True,  primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    room_size = Column(Float, nullable=False)
    description = Column(Text)
    adults = Column(Integer, nullable=False,  default=2)
    children = Column(Integer, default=1)
    price = Column(Double, nullable=False)
    rooms = relationship("Room", lazy=True, backref="type")
    amenities = relationship(
        "Amenity", secondary="amenity_room")
    images = relationship("Image", lazy=True)
    policies = relationship("Policy", secondary="roomtype_policy", lazy=True)

    def check_available(self, check_in, check_out):
        rooms = []

        if check_in and check_out:
            check_in = utils.string_to_date(check_in)
            check_out = utils.string_to_date(check_out)

            for room in self.rooms:
                bookings = [booking for booking in room.bookings if booking.created_at >=
                            datetime.now() - timedelta(days=30)]

                available = True
                for booking in bookings:
                    if not ((check_in < booking.check_in and check_out < booking.check_in) or check_in > booking.check_out):
                        available = False
                if available:
                    rooms.append(room)

        return rooms

    def __str__(self):
        return self.name

    def get_image(self):
        return self.images[randint(0, len(self.images) - 1)]

    def add_policy(self, policy):
        self.policies.append(policy)


class Image(db.Model):
    id = Column(Integer, autoincrement=True,  primary_key=True)
    src = Column(String(255), nullable=False)
    room_type = Column(Integer, ForeignKey(RoomType.id))


class BaseAmenity(db.Model):
    __abstract__ = True
    id = Column(Integer, autoincrement=True,  primary_key=True)
    amenity = Column(Integer, ForeignKey(Amenity.id), nullable=False)
    quantity = Column(Integer, default=1)


class AmenityRoom(BaseAmenity):
    room = Column(Integer, ForeignKey(RoomType.id), nullable=False)


class Room(db.Model):
    id = Column(Integer, autoincrement=True,  primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    room_type = Column(Integer, ForeignKey(RoomType.id), nullable=False)
    guests = relationship("BookingGuest", lazy=True)

    def __str__(self):
        return self.name

    def get_room_type(self):
        return self.type

    def get_price(self):
        return self.type.price

    def get_expense(self, booking_id):
        policies = self.get_room_type().policies

        expenses = [{"name": policy.name, "expense": policy.expense}
                    for policy in policies]
        guests = [guest for guest in self.guests if guest.booking_id == booking_id]
        capacity = self.get_room_type().adults
        if (capacity == 2 and len(guests) > capacity):
            expenses[1]['expense'] = self.get_price() * expenses[1]['expense']
        else:
            expenses[1]['expense'] = 0

        if any(not guest.get_guest().is_vietnamese for guest in guests):
            expenses[0]['expense'] = self.get_price() * expenses[0]['expense']
        else:
            expenses[0]['expense'] = 0
        return expenses

    def get_image(self):
        return self.type.get_image()


class Requirement (BaseAmenity):
    room = Column(Integer, ForeignKey(Room.id), nullable=False)
    reservation = Column(Integer, ForeignKey('reservation.id'), nullable=False)


class BaseForm(db.Model):
    __abstract__ = True
    id = Column(Integer, autoincrement=True,  primary_key=True)
    check_in = Column(Date, nullable=False, default=datetime.now)
    check_out = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class Booking(BaseForm):
    name = Column(String(50), nullable=False)
    phone = Column(String(11), nullable=False)
    email = Column(String(50), nullable=False)
    notes = Column(Text)
    receptionist = Column(Integer, ForeignKey(User.id))
    rooms = relationship(Room, secondary="booking_room", backref='bookings')
    guests = relationship("BookingGuest", backref="bookings")
    status = Column(Enum(BookingStatus), default=BookingStatus.CONFIRMED)
    reservation = relationship("Reservation", uselist=False)
    invoice = relationship("BookingInvoice", lazy=True, uselist=False)

    def add_room(self, room):
        self.rooms.append(room)

    def remove_room(self, room):
        self.rooms.remove(room)

    def get_guests(self):
        return self.guests

    def get_estimated_total(self):
        return sum(room.get_price() for room in self.rooms)

    def get_total(self):
        expenses = 0
        for room in self.rooms:
            expenses += sum(expense['expense']
                            for expense in room.get_expense(self.id))

        return sum(room.get_price() for room in self.rooms) + expenses

    def set_invoice_status(self, status):
        self.invoice.status = status
        db.session.commit()

    def create_invoice(self, receptionist):
        invoice = BookingInvoice(amount=self.get_total(
        ), booking=self.id, receptionist=receptionist)
        db.session.add(invoice)
        db.session.commit()


class Reservation(BaseForm):
    booking = Column(Integer, ForeignKey(Booking.id), unique=True)
    receptionist = Column(Integer, ForeignKey(User.id))
    rooms = relationship(Room, secondary="reservation_room",
                         backref='reservations')
    guests = relationship("ReservationGuest", backref="reservations")
    invoice = relationship("ReservationInvoice", lazy=True, uselist=False)

    def add_room(self, room):
        self.rooms.append(room)

    def get_guests(self):
        return self.guests

    def get_total(self):
        expenses = 0
        booking_paid = 0
        if self.booking:
            booking = Booking.query.get_or_404(self.booking)
            if booking.invoice.status == InvoiceStatus.PAID:
                booking_paid = booking.invoice.amount
        for room in self.rooms:
            expenses += sum(expense['expense']
                            for expense in room.get_expense(self.id))

        return sum(room.get_price() for room in self.rooms) + expenses - booking_paid

    def set_invoice_status(self, status):
        self.invoice.status = status
        db.session.commit()

    def create_invoice(self, receptionist):
        invoice = ReservationInvoice(amount=self.get_total(
        ), reservation=self.id, receptionist=receptionist)
        db.session.add(invoice)
        db.session.commit()


booking_room = Table("booking_room",
                     db.metadata,
                     Column('booking_id', Integer, ForeignKey(
                         Booking.id), primary_key=True),
                     Column('room_id', Integer, ForeignKey(Room.id), primary_key=True))


reservation_room = Table("reservation_room",
                         db.metadata,
                         Column('reservation_id', Integer, ForeignKey(
                             Reservation.id), primary_key=True),
                         Column('room_id', Integer, ForeignKey(Room.id), primary_key=True))


class BookingGuest(db.Model):
    id = Column(Integer, autoincrement=True,  primary_key=True)
    booking_id = Column(Integer, ForeignKey(Booking.id), nullable=False)
    guest_id = Column(Integer, ForeignKey(Guest.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    guest = relationship("Guest", backref="bookings")

    def get_guest(self):
        return self.guest

    def get_room(self):
        return Room.query.get(self.room_id)


class ReservationGuest(db.Model):
    id = Column(Integer, autoincrement=True,  primary_key=True)
    reservation_id = Column(Integer, ForeignKey(
        Reservation.id), nullable=False)
    guest_id = Column(Integer, ForeignKey(Guest.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)

    def get_guest(self):
        return Guest.query.get(self.guest_id)

    def get_room(self):
        return Room.query.get(self.room_id)


class Invoice(db.Model):
    __abstract__ = True
    receptionist = Column(Integer, ForeignKey(User.id))
    amount = Column(Double, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING)


class BookingInvoice(Invoice):
    booking = Column(Integer, ForeignKey(Booking.id), primary_key=True)


class ReservationInvoice(Invoice):
    reservation = Column(Integer, ForeignKey(Reservation.id), primary_key=True)


class Policy(db.Model):
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50))
    details = Column(Text)
    expense = Column(Double)
    creator = Column(Integer, ForeignKey(User.id))


roomtype_policy = Table("roomtype_policy",
                        db.metadata,
                        Column('room_type', Integer, ForeignKey(
                            RoomType.id), primary_key=True),
                        Column('policy_id', Integer, ForeignKey(Policy.id), primary_key=True))


class Issue(db.Model):
    id = Column(Integer, autoincrement=True, primary_key=True)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    room = Column(Integer, ForeignKey(Room.id), nullable=False)
    reservation = Column(Integer, ForeignKey(Reservation.id), nullable=False)
    policy = Column(Integer, ForeignKey(Policy.id))


class Review(db.Model):
    id = Column(Integer, autoincrement=True, primary_key=True)
    reservation = Column(Integer, ForeignKey(Reservation.id), nullable=False)
    content = Column(Text)
    rating = Column(Enum(Rating), default=Rating.VERY_GOOD)
    created_at = Column(DateTime, default=datetime.now)


class Service(db.Model):
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50))
    details = Column(Text)
    price = Column(Double, nullable=False)
    unit = Column(String(20))


class ReservationService(db.Model):
    id = Column(Integer, autoincrement=True, primary_key=True)
    reservation = Column(Integer, ForeignKey(Reservation.id), nullable=False)
    service = Column(Integer, ForeignKey(Service.id), nullable=False)
    quantity = Column(Double, default=1)
    staff = Column(Integer, ForeignKey(ServiceStaff.id))


def clear_data(db):
    db.drop_all()
    db.session.commit()


def insert_data(db, obj, fileName):
    with open(f'data/{fileName}.json', encoding='utf-8') as f:
        items = json.load(f)
        for item in items:
            db.session.add(obj(**item))
    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        clear_data(db)
        db.create_all()

        with open(f'data/users.json', encoding='utf-8') as f:
            items = json.load(f)
            for item in items:
                first_name = item['first_name']
                last_name = item['last_name']
                address = item['address']
                identity_num = item['identity_num']
                phone = item['phone']
                email = item['email']
                password = str(hashlib.md5(
                    item['password'].encode('utf-8')).hexdigest())

                if phone.__eq__("335037042"):
                    db.session.add(User(first_name=first_name, name=last_name, address=address,
                                        identity_num=identity_num, phone=phone, email=email, password=password, role=UserRole.ADMIN, avatar="https://res.cloudinary.com/dzjhqjxqj/image/upload/v1703844016/v2depwkhte1trcs0z9q9.jpg"))
                elif phone.__eq__("987654999"):
                    db.session.add(User(first_name=first_name, name=last_name, address=address,
                                        identity_num=identity_num, phone=phone, email=email, password=password, role=UserRole.RECEPTIONIST))
                else:
                    db.session.add(User(first_name=first_name, name=last_name, address=address,
                                        identity_num=identity_num, phone=phone, email=email, password=password))

            db.session.commit()

        # password = str(hashlib.md5("Admin@123".encode('utf-8')).hexdigest())
        # db.session.add(User(first_name="vuong", name="pham", address="tayninh",
        #                     identity_num="07220300000", phone="0843751500", email="admin@admin.com", password=password, role=UserRole.ADMIN))
        insert_data(db, RoomType, "room-types")
        insert_data(db, Room, "room")
        insert_data(db, AmenityType, "amenity-types")
        insert_data(db, Amenity, "amenity")
        insert_data(db, AmenityRoom, "amenity-room")
        insert_data(db, Image, "image")
        insert_data(db, Guest, 'guest')
        insert_data(db, Policy, 'policy')

        insert_data(db, Booking, "booking")
        with open(f'data/booking-room.json', encoding='utf-8') as f:
            items = json.load(f)
            for item in items:
                booking = Booking.query.get_or_404(item['booking_id'])
                room = Room.query.get_or_404(item['room_id'])
                booking.add_room(room=room)
        insert_data(db, BookingGuest, 'booking-guest')

        insert_data(db, Reservation, "reservation")
        with open(f'data/reservation-room.json', encoding='utf-8') as f:
            items = json.load(f)
            for item in items:
                reservation = Reservation.query.get_or_404(
                    item['reservation_id'])
                room = Room.query.get_or_404(item['room_id'])
                reservation.add_room(room=room)
        insert_data(db, ReservationGuest, 'reservation-guest')

        with open(f'data/roomtype-policy.json', encoding='utf-8') as f:
            items = json.load(f)
            for item in items:
                room_type = RoomType.query.get_or_404(item['room_type'])
                policy = Policy.query.get_or_404(item['policy_id'])
                room_type.add_policy(policy=policy)

        for booking in Booking.query.all():
            booking.create_invoice(2)

        for reservation in Reservation.query.all():
            reservation.create_invoice(2)
        # for i in range(10):
        #     booking = Booking.query.get_or_404(i+1)
        #     for y in range(2):
        #         booking.add_room(room=Room.query.get_or_404(y + randint(1, 28)))
        db.session.commit()
