from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy import Enum
from extensions import db
from datetime import datetime
from sqlalchemy.sql import func

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, autoincrement=True ,primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(Enum('Customer', 'Admin', 'Staff', name='role_enum'), nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)

    __mapper_args__ = {
        'polymorphic_on': role,
        'polymorphic_identity': 'User'
    }
    def __str__(self):
        return self.username
    
class Admin(User):
    __mapper_args__ = {
        'polymorphic_identity': 'Admin'
    }
    rules = relationship('Rule', backref='admin', lazy=True)

class Staff(User):
    __mapper_args__ = {
        'polymorphic_identity': 'Staff'
    }

class Customer(User):
    __mapper_args__ = {
        'polymorphic_identity': 'Customer'
    }
    bookings = relationship('Booking', backref='customer', lazy=True)

class Rule(db.Model):
    __tablename__ = 'rules'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    quantity_airport = db.Column(db.Integer, nullable=False)
    min_flight_time = db.Column(db.Integer, nullable=False)
    max_intermediate_airport = db.Column(db.Integer, nullable=False)
    min_stop_time = db.Column(db.Integer, nullable=False)
    max_stop_time = db.Column(db.Integer, nullable=False)
    time_buy = db.Column(db.Integer, nullable=False)
    time_sell = db.Column(db.Integer, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __str__(self):
        return f'Rule - {self.id}'


class Flight(db.Model):
    __tablename__ = 'flights'
    id=db.Column(db.String(10), primary_key=True)
    start_location = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    flight_schedules = relationship('FlightSchedule', backref='flight', lazy=True)

    # Khóa ngoại chỉ ra sân bay đến và sân bay khởi hành
    start_location_id = db.Column(db.String(10), ForeignKey('airports.abbreviate_name'))  # Khóa ngoại cho sân bay khởi hành
    destination_id = db.Column(db.String(10), ForeignKey('airports.abbreviate_name'))  # Khóa ngoại cho sân bay đến

    # Mối quan hệ nhiều - một với sân bay khởi hành và sân bay đến
    airport_departure = relationship('Airport', foreign_keys=[start_location_id], back_populates='departure_flights')
    airport_arrival = relationship('Airport', foreign_keys=[destination_id], back_populates='arrival_flights')

    def __str__(self):
        return f"{self.start_location} - {self.destination}"
    

class Airport(db.Model):
    __tablename__ = 'airports'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    abbreviate_name = db.Column(db.String(10), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False, unique = True)
    location = db.Column(db.String(100), nullable=False)
    nation = db.Column(db.String(100), nullable=False)

    # Các mối quan hệ với Flight (khởi hành và đến)
    departure_flights = relationship('Flight', back_populates='airport_departure', foreign_keys=[Flight.start_location_id])
    arrival_flights = relationship('Flight', back_populates='airport_arrival', foreign_keys=[Flight.destination_id])

    def __str__(self):
        return self.name


class FlightSchedule(db.Model):
    __tablename__ = 'flight_schedules'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    start_date = db.Column(db.DateTime, nullable=False)
    flight_id = db.Column(db.String(10), db.ForeignKey('flights.id', ondelete="CASCADE"), nullable=False)
    flight_time = db.Column(db.Float, nullable=False)
    tickets = relationship('Ticket', backref='flight_schedule', lazy=True)
    intermediate_airports = relationship('IntermediateAirport', backref='flight_schedule', lazy=True)
    booking_id = relationship('Booking', backref='flight_schedule', lazy=True)

    
    def total_tickets_by_class(self):
        # Tính tổng số vé cho từng loại vé
        ticket_totals = {}
        for ticket in self.tickets:
            total_quantity = ticket.quantity
            ticket_totals[ticket.ticket_class] = total_quantity
        return ticket_totals


    def __str__(self):
        return f"FlightSchedule {self.id} - {self.start_date}"


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    identity_card = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.Integer, nullable=False)
    booking_date = db.Column(
        db.DateTime, 
        server_default=func.now(), 
        nullable=False
    )
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    flight_schedule_id = db.Column(db.Integer, db.ForeignKey('flight_schedules.id'), nullable=False)
    payment = relationship('Payment', backref='booking', uselist=False, lazy=True)
    
    # Quan hệ nhiều - nhiều với Ticket qua bảng BookingTicket
    tickets = relationship('BookingTicket', back_populates='booking', lazy=True)

    def __str__(self):
        return f"Booking of {self.fullname} - flightschedule {self.flight_schedule_id}"

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    ticket_class = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    flight_schedule_id = db.Column(db.Integer, db.ForeignKey('flight_schedules.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)  # Số lượng vé của loại này

    # Quan hệ nhiều - nhiều với Booking qua bảng BookingTicket
    bookings = relationship('BookingTicket', back_populates='ticket', lazy=True)

    def __str__(self):
        return f"Ticket class {self.ticket_class} of {self.flight_schedule_id}"

class Seat(db.Model):
    __tablename__ = 'seats'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    seat_number = db.Column(db.String(10), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='available')
    booking_ticket_id = db.Column(db.Integer, db.ForeignKey('booking_tickets.id'), nullable=True)

    booking_ticket = relationship('BookingTicket', back_populates='seat')

class BookingTicket(db.Model):
    __tablename__ = 'booking_tickets'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)

    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    # Quan hệ với Booking và Ticket
    booking = relationship('Booking', back_populates='tickets')
    ticket = relationship('Ticket', back_populates='bookings')

    # Quan hệ với Seat
    seat = relationship('Seat', back_populates='booking_ticket', lazy=True)

    def __str__(self):
        return f"Booking {self.booking_id} - Ticket {self.ticket_id} - Quantity {self.quantity}"


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)

    def __str__(self):
        return f"Payment of {self.booking_id}"

class IntermediateAirport(db.Model):
    __tablename__ = 'intermediate_airports'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    note = db.Column(db.String(255), nullable=True)
    stop_time = db.Column(db.Integer, nullable=False)
    airport_id = db.Column(db.String(10), db.ForeignKey('airports.abbreviate_name', ondelete="CASCADE"), nullable=False)
    flight_schedule_id = db.Column(db.Integer, db.ForeignKey('flight_schedules.id', ondelete="CASCADE"), nullable=False)
    airport = relationship('Airport', backref='intermediate_airports')

    def __str__(self):
        return f"IntermediateAirport {self.id}"
