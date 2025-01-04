from flask import Flask
from pymysql import IntegrityError
from authentication_routes import authentication_routes
from register import register_bp
from chuyen_bay_routes import chuyen_bay_routes
from dat_ve_routes import dat_ve_routes
from ban_ve_routes import ban_ve_routes
from lich_chuyen_bay_routes import lich_chuyen_bay_routes
from ve_chuyen_bay_routes import ve_chuyen_bay_routes
from quy_dinh_routes import quy_dinh_routes
from san_bay_routes import san_bay_routes
from extensions import db
from forgot import ForgotPassword
from models import Customer, Staff, User, Admin, Flight, FlightSchedule, IntermediateAirport, Airport, Booking, Payment, Rule, Ticket, BookingTicket, Seat
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView



app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/airlineticket_db5?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db.init_app(app)


# Register the authentication routes Blueprint
app.register_blueprint(authentication_routes, url_prefix='/')
app.register_blueprint(register_bp, url_prefix='/')
app.register_blueprint(ForgotPassword, url_prefix='/')
app.register_blueprint(dat_ve_routes, url_prefix='/')
app.register_blueprint(chuyen_bay_routes, url_prefix='/')
app.register_blueprint(ban_ve_routes, url_prefix='/')
app.register_blueprint(lich_chuyen_bay_routes, url_prefix='/')
app.register_blueprint(ve_chuyen_bay_routes, url_prefix='/')
app.register_blueprint(quy_dinh_routes, url_prefix='/')
app.register_blueprint(san_bay_routes, url_prefix='/')

admin = Admin(app, name="Admin Flight Booking", template_mode="bootstrap4")


class MyFlightView(ModelView):
    column_list = ['id', 'destination', 'start_location', 'flight_schedules', 'airport_departure', 'airport_arrival']
    form_columns = ['id','destination', 'start_location', 'flight_schedules', 'airport_departure', 'airport_arrival']
    form_widget_args = {
        'id': {
            'readonly': False  # Đảm bảo cột này có thể nhập liệu
        }
    }

class MyBookingView(ModelView):
    column_list = ['id', 'booking_date', 'ticket', 'payment', 'customer_id', 'flight_id', 'ticket']

class MyAirportView(ModelView):
    column_list = ['id', 'name', 'location', 'nation']


admin.add_view(MyFlightView(Flight, db.session))
admin.add_view(ModelView(FlightSchedule, db.session))
admin.add_view(ModelView(IntermediateAirport, db.session))
admin.add_view(ModelView(Airport, db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Staff, db.session))
admin.add_view(ModelView(Customer, db.session))
admin.add_view(ModelView(Rule, db.session))
admin.add_view(ModelView(Ticket, db.session))
admin.add_view(MyBookingView(Booking, db.session))
admin.add_view(ModelView(Payment, db.session))
admin.add_view(ModelView(BookingTicket, db.session))
admin.add_view(ModelView(Seat, db.session))

if __name__ == '__main__':
    with app.app_context(): 
        db.create_all()
        app.run(debug=True)
