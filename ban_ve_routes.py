from flask import Blueprint, render_template, redirect, url_for, flash, session, request
# from db_utils import cursor, db
from datetime import datetime, timedelta
from extensions import db
from models import Airport, Flight, FlightSchedule, Ticket, Rule, Booking, BookingTicket, Payment
from sqlalchemy.orm import aliased
from sqlalchemy import func

ban_ve_routes = Blueprint('ban_ve_routes', __name__)
AirportStart = aliased(Airport)
AirportDest = aliased(Airport)


@ban_ve_routes.route('/danh_sach_ban_ve')
def danh_sach_ban_ve():
     # Lấy danh sách sân bay ngay từ đầu, luôn có dữ liệu
    airport_departure_list = db.session.query(Airport).join(Flight, Flight.start_location_id == Airport.abbreviate_name).distinct().all()
    airport_arrival_list = db.session.query(Airport).join(Flight, Flight.destination_id == Airport.abbreviate_name).distinct().all()

    # Dữ liệu tìm kiếm (nếu có)
    airport_departure_selected = request.args.get('airport_departure', '')
    airport_arrival_selected = request.args.get('airport_arrival', '')
    start_date = request.args.get('start_date', '')

     # Tìm kiếm chuyến bay
    query = db.session.query(
        Flight.id,
        AirportStart.name.label('start_airport_name'),  # Tên sân bay khởi hành
        AirportDest.name.label('destination_airport_name'),  # Tên sân bay đến
        FlightSchedule.start_date,
        Ticket.price,
        Ticket.id.label('ticket_id'),
        Ticket.ticket_class,
        FlightSchedule.id.label('flight_schedule_id')
    ).join(
        AirportStart, Flight.start_location_id == AirportStart.abbreviate_name  # Join sân bay khởi hành
    ).join(
        AirportDest, Flight.destination_id == AirportDest.abbreviate_name  # Join sân bay đến
    ).join(
        FlightSchedule, Flight.id == FlightSchedule.flight_id
    ).join(
        Ticket, Flight.id == Ticket.flight_id
    )

    # Áp dụng bộ lọc nếu có
    if airport_departure_selected:
        query = query.filter(Flight.start_location_id  == airport_departure_selected)
    if airport_arrival_selected:
        query = query.filter(Flight.destination_id  == airport_arrival_selected)
    if start_date:
        try:
            start_date_new = datetime.strptime(start_date, '%Y-%m-%d')
            day_start = datetime.combine(start_date_new, datetime.min.time())
            day_end = datetime.combine(start_date_new, datetime.max.time())

            query = query.filter(
                (FlightSchedule.start_date >= day_start) &
                (FlightSchedule.start_date <= day_end)
            )
        except ValueError:
            flash('Ngày khởi hành không hợp lệ. Vui lòng nhập đúng định dạng YYYY-MM-DD.')

    # Lấy điều kiện so_gio_dat_ve_truoc từ bảng QuyDinh
    rule = Rule.query.first()
    if rule:
        query = query.filter(
            db.func.timestampdiff(db.text('HOUR'), datetime.now(), FlightSchedule.start_date) >= Rule.time_buy
        )

    flight_list = query.all()

    # Lấy quyền từ session
    role = session.get('user', {}).get('role', 'Customer')

    return render_template(
        'danh_sach_ban_ve.html',
        airport_departure_list=airport_departure_list,
        airport_arrival_list=airport_arrival_list,
        airport_departure_selected=airport_departure_selected,
        airport_arrival_selected=airport_arrival_selected,
        start_date=start_date,
        flight_list=flight_list,
        role=role
    )



@ban_ve_routes.route('/thong_tin_ve/<booking_id>', methods=['GET'])
def thong_tin_ve(booking_id):
    try:
        # Truy vấn thông tin đặt vé từ bảng Booking
        booking = db.session.query(Booking).filter(Booking.id == booking_id).first()

        if booking:
            # Thông tin đặt vé
            booking_info = {
                "fullname": booking.fullname,
                "identity_card": booking.identity_card,
                "phone_number": booking.phone_number,
                "id": booking.id,
                "schedule_flight_id": booking.flight_schedule_id,
                "date_booking": booking.booking_date.strftime("%d-%m-%Y %H:%M:%S")
            }
            
            # Lấy thông tin lịch chuyến bay
            flight_schedule = booking.flight_schedule
            flight_info = {
                "airport_departure": flight_schedule.flight.airport_departure.name,
                "airport_arrival": flight_schedule.flight.airport_arrival.name,
                "start_date": flight_schedule.start_date.strftime("%d-%m-%Y %H:%M:%S"),
                "flight_time": flight_schedule.flight_time
            }

            # Tạo chuỗi HTML cho danh sách vé
            ticket_details_html = ""
            total_quantity = 0
            for booking_ticket in booking.tickets:
                ticket = booking_ticket.ticket
                total_quantity += booking_ticket.quantity
                ticket_details_html += f"""
                <tr>
                    <td>{ticket.ticket_class}</td>
                    <td>{ "{:,.0f}".format(ticket.price).replace(",", ".")} VND</td>
                    <td>{ticket.flight_id}</td>
                    <td>{booking_ticket.quantity}</td>
                </tr>
                """

            # Lấy tổng số tiền từ bảng Payment
            total_amount = booking.payment.amount if booking.payment else 0

            # Lấy quyền của người dùng từ session
            role = session.get('user', {}).get('role', 'Customer')


            return render_template(
                'thong_tin_ve.html',
                booking_info=booking_info,
                flight_info=flight_info,
                total_quantity=total_quantity,
                total_amount=total_amount,
                ticket_details_html=ticket_details_html,  # Truyền chuỗi HTML vào template
                role=role
            )
        else:
            flash('Không tìm thấy thông tin đặt vé.')
            return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))
    except Exception as e:
        flash(f'Đã xảy ra lỗi: {str(e)}')
        return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))


