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
    
@ban_ve_routes.route('/ban_ve/<id>/<schedule_flight_id>', methods=['GET', 'POST'])
def ban_ve(id, schedule_flight_id):
    role = session.get('user', {}).get('role', 'Customer')

    if request.method == 'GET':
        # Lấy thông tin vé và các liên kết khác
        ticket = db.session.query(Ticket)\
            .join(Flight, Ticket.flight_id == Flight.id)\
            .join(FlightSchedule, Flight.id == FlightSchedule.flight_id)\
            .filter(Ticket.id == id).first()

        schedule_flight = FlightSchedule.query.filter_by(id=schedule_flight_id).first()

        rule = db.session.query(Rule).first()

        if not ticket or not rule:
            flash('Không tìm thấy thông tin chuyến bay hoặc quy định.')
            return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))

        # Kiểm tra thời gian đặt vé
        time_sell = schedule_flight.start_date - timedelta(hours=rule.time_sell)
        if datetime.now() >= time_sell:
            flash('Không thể bán vé cho chuyến bay này do đã quá thời gian bán vé.')
            return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))

         # Tính số ghế đã đặt cho Hạng 1
        booked_seats_class_1 = db.session.query(func.sum(BookingTicket.quantity))\
                    .join(Ticket, BookingTicket.ticket_id == Ticket.id)\
                    .join(Booking, BookingTicket.booking_id == Booking.id)\
                    .filter(Booking.flight_schedule_id == schedule_flight_id, Ticket.ticket_class == 'Hạng 1')\
                    .scalar() or 0  # Trả về 0 nếu không có vé nào được đặt

        booked_seats_class_2 = db.session.query(func.sum(BookingTicket.quantity))\
                    .join(Ticket, BookingTicket.ticket_id == Ticket.id)\
                    .join(Booking, BookingTicket.booking_id == Booking.id)\
                    .filter(Booking.flight_schedule_id == schedule_flight_id, Ticket.ticket_class == 'Hạng 2')\
                    .scalar() or 0

        # Kiểm tra ghế còn trống
        quantity_class_1 = schedule_flight.quantity_class1
        quantity_class_2 = schedule_flight.quantity_class2

        if booked_seats_class_1 < quantity_class_1 or booked_seats_class_2 < quantity_class_2:
            return render_template('ban_ve.html', ticket=ticket, schedule_flight_id=schedule_flight_id, role=role)

        flash('Không thể đặt vé cho chuyến bay này do hết chỗ.')
        return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))

    elif request.method == 'POST':
        # Lấy thông tin từ form
        customer_id = session.get('user', {}).get('id')  # Lấy id người dùng từ session
        if not customer_id:
            flash('Bạn cần đăng nhập để thực hiện thanh toán.', 'error')
            return redirect(url_for('auth.login'))
        fullname = request.form['fullname']
        identity_card = request.form['identity_card']
        phone_number = request.form['phone_number']
        amount = float(request.form.get('price', 0))
        id_post = request.form['id']
        quantity = int(request.form.get('quantity', 1))

        # Kiểm tra thông tin vé
        ticket = db.session.query(Ticket)\
            .join(Flight, Ticket.flight_id == Flight.id)\
            .join(FlightSchedule, Flight.id == FlightSchedule.flight_id)\
            .filter(Ticket.id == id).first()
            
        schedule_flight = FlightSchedule.query.filter_by(id=schedule_flight_id).first()

        rule = db.session.query(Rule).first()

        if not ticket or not rule:
            flash('Không tìm thấy thông tin chuyến bay hoặc quy định.')
            return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))


        # Kiểm tra thời gian bán vé
        time_sell = schedule_flight.start_date - timedelta(hours=rule.time_sell)
        if datetime.now() >= time_sell:
            flash('Không thể bán vé cho chuyến bay này do đã quá thời gian bán vé.')
            return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))

        # Tính số ghế đã đặt cho Hạng 1
        booked_seats_class_1 = db.session.query(func.sum(BookingTicket.quantity))\
                    .join(Ticket, BookingTicket.ticket_id == Ticket.id)\
                    .join(Booking, BookingTicket.booking_id == Booking.id)\
                    .filter(Booking.flight_schedule_id == schedule_flight_id, Ticket.ticket_class == 'Hạng 1')\
                    .scalar() or 0  # Trả về 0 nếu không có vé nào được đặt

        booked_seats_class_2 = db.session.query(func.sum(BookingTicket.quantity))\
                    .join(Ticket, BookingTicket.ticket_id == Ticket.id)\
                    .join(Booking, BookingTicket.booking_id == Booking.id)\
                    .filter(Booking.flight_schedule_id == schedule_flight_id, Ticket.ticket_class == 'Hạng 2')\
                    .scalar() or 0

        # Lấy tổng số ghế của từng hạng từ thông tin chuyến bay
        quantity_class_1 = schedule_flight.quantity_class1
        quantity_class_2 = schedule_flight.quantity_class2

        # Kiểm tra ghế trống
        if booked_seats_class_1 >= quantity_class_1 and booked_seats_class_2 >= quantity_class_2:
            flash('Không thể đặt vé cho chuyến bay này do hết chỗ.')
            return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))
        
        # Tạo thông tin đặt vé
        booking = Booking(
            fullname=fullname,  # Sửa "fullname" thành "fullname" theo tên cột trong model
            identity_card=identity_card,  # Sửa "identity_card" thành "identity_card"
            phone_number=phone_number,  # Sửa "phone_number" thành "phone_number"
            customer_id=customer_id,  # Thay bằng thông tin khách hàng liên quan
            flight_schedule_id=schedule_flight_id  # Sửa "schedule_flight_id" thành "flight_schedule_id"
        )
        
        db.session.add(booking)
        db.session.commit()

        # Lấy mã đặt vé vừa được thêm
        booking_id = booking.id

        booking_ticket = BookingTicket(
            booking_id=booking_id,
            ticket_id=id_post,
            quantity=quantity
        )
        db.session.add(booking_ticket)
        db.session.commit()

        # Thêm thông tin thanh toán
        
        thanh_toan = Payment(
            booking_id=booking_id, 
            amount=amount,  
            payment_method='Tại quầy',  
            payment_date=datetime.utcnow(), 
        )
        db.session.add(thanh_toan)
        db.session.commit()

        flash('Bán vé và thanh toán thành công.')
        return redirect(url_for('ban_ve_routes.thong_tin_ve', booking_id=booking_id))


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


