from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from datetime import datetime, timedelta
from extensions import db
from models import Airport, Flight, FlightSchedule, Ticket, Rule, Booking, BookingTicket, Payment, Seat
from sqlalchemy.orm import aliased
from sqlalchemy import func, case

ban_ve_routes = Blueprint('ban_ve_routes', __name__)
AirportStart = aliased(Airport)
AirportDest = aliased(Airport)


@ban_ve_routes.route('/danh_sach_ban_ve')
def danh_sach_ban_ve():
    username = session['user']['username']
    airport_departure_list = db.session.query(Airport).join(Flight, Flight.start_location_id == Airport.abbreviate_name).distinct().all()
    airport_arrival_list = db.session.query(Airport).join(Flight, Flight.destination_id == Airport.abbreviate_name).distinct().all()

    # Dữ liệu tìm kiếm (nếu có)
    airport_departure_selected = request.args.get('airport_departure', '')
    airport_arrival_selected = request.args.get('airport_arrival', '')
    start_date = request.args.get('start_date', '')

    # Tìm kiếm chuyến bay
    query = db.session.query(
        Flight.id,
        AirportStart.name.label('start_airport_name'),
        AirportDest.name.label('destination_airport_name'),
        FlightSchedule.start_date,
        Ticket.price,
        Ticket.id.label('ticket_id'),
        Ticket.ticket_class,
        FlightSchedule.id.label('flight_schedule_id'),
        (
            case(
                (Ticket.ticket_class == '1', func.coalesce(Ticket.quantity, 0)),
                (Ticket.ticket_class == '2', func.coalesce(Ticket.quantity, 0)),
                else_=0
            ) - func.coalesce(func.sum(BookingTicket.quantity), 0)
        ).label('remaining_tickets')
    ).join(
        AirportStart, Flight.start_location_id == AirportStart.abbreviate_name
    ).join(
        AirportDest, Flight.destination_id == AirportDest.abbreviate_name
    ).join(
        FlightSchedule, Flight.id == FlightSchedule.flight_id
    ).join(
        Ticket, FlightSchedule.id == Ticket.flight_schedule_id
    ).outerjoin(
        BookingTicket, BookingTicket.ticket_id == Ticket.id
    ).group_by(
        Flight.id, AirportStart.name, AirportDest.name,
        FlightSchedule.start_date, Ticket.price, Ticket.id,
        Ticket.ticket_class, FlightSchedule.id
    )


    # Áp dụng bộ lọc nếu có
    if airport_departure_selected:
        query = query.filter(Flight.start_location_id  == airport_departure_selected)
    if airport_arrival_selected:
        query = query.filter(Flight.destination_id  == airport_arrival_selected)
    if start_date:
        try:
            start_date_date = datetime.strptime(start_date, '%Y-%m-%d')
            ngay_bat_dau = datetime.combine(start_date_date, datetime.min.time())
            ngay_ket_thuc = datetime.combine(start_date_date, datetime.max.time())

            query = query.filter(
                (FlightSchedule.start_date >= ngay_bat_dau) &
                (FlightSchedule.start_date <= ngay_ket_thuc)
            )
        except ValueError:
            flash('Ngày khởi hành không hợp lệ. Vui lòng nhập đúng định dạng YYYY-MM-DD.')



    query = query.filter(
        db.func.timestampdiff(
            db.text('HOUR'), db.func.now(), FlightSchedule.start_date
        ) >= db.session.query(Rule.time_sell).scalar()
    )

    flight_list = query.all()

    # Kiểm tra nếu không có chuyến bay nào được tìm thấy
    if not flight_list:
        flash('Không có chuyến bay phù hợp với lịch trình đã chọn. Vui lòng thử chọn lịch trình khác.', 'warning')

    role = session.get('user', {}).get('role', 'Staff')
    return render_template(
        'danh_sach_ban_ve.html',
        airport_departure_list=airport_departure_list,
        airport_arrival_list=airport_arrival_list,
        airport_departure_selected=airport_departure_selected,
        airport_arrival_selected=airport_arrival_selected,
        start_date=start_date,
        flight_list=flight_list,
        role=role,
        username=username
    )
    
@ban_ve_routes.route('/ban_ve/<id>/<schedule_flight_id>', methods=['GET', 'POST'])
def ban_ve(id, schedule_flight_id):
    role = session.get('user', {}).get('role', 'Staff')
    username = session['user']['username']

    if request.method == 'GET':
        # Lấy thông tin vé và lịch trình chuyến bay
        ticket_flight = Ticket.query.filter_by(id=id).first()
        schedule_flight = FlightSchedule.query.filter_by(id=schedule_flight_id).first()
        rule = Rule.query.first()

        if not ticket_flight or not schedule_flight or not rule:
            flash('Không tìm thấy thông tin vé, chuyến bay hoặc quy định.')
            return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))

        # Kiểm tra thời gian bán vé
        time_sell = schedule_flight.start_date - timedelta(hours=rule.time_sell)
        if datetime.now() >= time_sell:
            flash('Không thể bán vé cho chuyến bay này do đã quá thời gian bán vé.')
            return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))

        # Tính số ghế đã đặt theo từng hạng
        total_seats_class_1 = int(db.session.query(func.sum(Ticket.quantity))
                    .filter_by(flight_schedule_id=schedule_flight_id, ticket_class='1').scalar() or 0)

        total_seats_class_2 = int(db.session.query(func.sum(Ticket.quantity))
            .filter_by(flight_schedule_id=schedule_flight_id, ticket_class='2').scalar() or 0)

        # Tính số ghế đã đặt cho từng hạng theo lịch trình
        booked_seats_class_1 = int(db.session.query(func.sum(BookingTicket.quantity))
            .join(Ticket, BookingTicket.ticket_id == Ticket.id)
            .join(Booking, BookingTicket.booking_id == Booking.id)
            .filter(Booking.flight_schedule_id == schedule_flight_id, Ticket.ticket_class == '1')
            .scalar() or 0)

        booked_seats_class_2 = int(db.session.query(func.sum(BookingTicket.quantity))
            .join(Ticket, BookingTicket.ticket_id == Ticket.id)
            .join(Booking, BookingTicket.booking_id == Booking.id)
            .filter(Booking.flight_schedule_id == schedule_flight_id, Ticket.ticket_class == '2')
            .scalar() or 0)

        # Lấy danh sách ghế đã đặt cho từng hạng
        booked_seats_list_class_1 = db.session.query(Seat.seat_number).join(BookingTicket, Seat.booking_ticket_id == BookingTicket.id) \
            .join(Ticket, BookingTicket.ticket_id == Ticket.id) \
            .join(Booking, BookingTicket.booking_id == Booking.id) \
            .filter(Booking.flight_schedule_id == schedule_flight_id, Ticket.ticket_class == '1') \
            .all()

        booked_seats_list_class_2 = db.session.query(Seat.seat_number).join(BookingTicket, Seat.booking_ticket_id == BookingTicket.id) \
            .join(Ticket, BookingTicket.ticket_id == Ticket.id) \
            .join(Booking, BookingTicket.booking_id == Booking.id) \
            .filter(Booking.flight_schedule_id == schedule_flight_id, Ticket.ticket_class == '2') \
            .all()

        # Chuyển đổi kết quả truy vấn thành danh sách các số ghế
        booked_seats_list_class_1 = [seat[0] for seat in booked_seats_list_class_1]
        booked_seats_list_class_2 = [seat[0] for seat in booked_seats_list_class_2]

        # Kiểm tra số ghế còn lại
        remaining_tickets_class_1 = total_seats_class_1 - booked_seats_class_1
        remaining_tickets_class_2 = total_seats_class_2 - booked_seats_class_2

        if remaining_tickets_class_1 > 0 or remaining_tickets_class_2 > 0:
            template = 'ban_ve_hang_1.html' if ticket_flight.ticket_class == '1' else 'ban_ve_hang_2.html'
            return render_template(template, 
                                    ticket_flight=ticket_flight,
                                    schedule_flight=schedule_flight,
                                    role=role, 
                                    remaining_tickets_class_1=remaining_tickets_class_1,
                                    remaining_tickets_class_2=remaining_tickets_class_2,
                                    total_seats_class_1=total_seats_class_1,
                                    total_seats_class_2=total_seats_class_2,
                                    booked_seats_list_class_1=booked_seats_list_class_1,
                                    booked_seats_list_class_2=booked_seats_list_class_2,
                                    username=username)
        else:
            flash('Chuyến bay này đã hết vé.')
            return redirect(url_for('dat_ve_routes.danh_sach_ban_ve'))


    elif request.method == 'POST':
        # Lấy thông tin từ form
        customer_id = session.get('user', {}).get('id')  
        if not customer_id:
            flash('Bạn cần đăng nhập để thực hiện thanh toán.', 'error')
            return redirect(url_for('auth.login'))

        fullname = request.form['fullname']
        identity_card = request.form['identity_card']
        phone_number = request.form['phone_number']
        seat_numbers_str = request.form.get('seat_numbers')  
        seat_numbers = seat_numbers_str.replace("[", "").replace("]", "").replace("'", "").split(',')
        raw_price = request.form.get('amount', "0")
        cleaned_price = raw_price.replace(".", "").replace(" VNĐ", "").strip()
        try:
            amount = float(cleaned_price)
        except ValueError:
            flash('Giá trị tiền không hợp lệ!')
            return redirect(url_for('ban_ve_routes.ban_ve', id=id, schedule_flight_id=schedule_flight_id))

        quantity = int(request.form.get('quantity', 1))

        # Kiểm tra vé và lịch trình chuyến bay
        ticket = Ticket.query.filter_by(id=id).first()
        schedule_flight = FlightSchedule.query.filter_by(id=schedule_flight_id).first()
        rule = Rule.query.first()

        if not ticket or not schedule_flight or not rule:
            flash('Không tìm thấy thông tin vé, chuyến bay hoặc quy định.')
            return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))

        # Kiểm tra thời gian bán vé
        time_sell = schedule_flight.start_date - timedelta(hours=rule.time_sell)
        if datetime.now() >= time_sell:
            flash('Không thể bán vé cho chuyến bay này do đã quá thời gian bán vé.')
            return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))

        # Kiểm tra số lượng vé còn lại
        booked_seats = db.session.query(func.sum(BookingTicket.quantity)) \
            .join(Ticket, BookingTicket.ticket_id == Ticket.id) \
            .join(Booking, BookingTicket.booking_id == Booking.id) \
            .filter(Booking.flight_schedule_id == schedule_flight_id,
                    Ticket.ticket_class == ticket.ticket_class) \
            .scalar() or 0

        if ticket.ticket_class == '1':
            total_seats = Ticket.query.filter_by(ticket_class='1').first().quantity
        elif ticket.ticket_class == '2':
            total_seats = Ticket.query.filter_by(ticket_class='2').first().quantity
        else:
            total_seats = 0


        remaining_tickets = total_seats - booked_seats
        if quantity > remaining_tickets:
            flash(f'Không thể bán {quantity} vé. Chỉ còn {remaining_tickets} vé trong chuyến bay này.')
            return redirect(url_for('ban_ve_routes.ban_ve', id=id, schedule_flight_id=schedule_flight_id))

        # Thêm thông tin đặt vé
        booking = Booking(
            fullname=fullname,
            identity_card=identity_card,
            phone_number=phone_number,
            customer_id=customer_id,
            flight_schedule_id=schedule_flight_id
        )
        db.session.add(booking)
        db.session.commit()

        # Tạo thông tin vé đặt
        booking_ticket = BookingTicket(
            booking_id=booking.id,
            ticket_id=ticket.id,
            quantity=quantity
        )
        db.session.add(booking_ticket)
        db.session.commit()

        for seat_number in seat_numbers:
            seat_number = seat_number.strip()  
            if seat_number:  
                new_seat = Seat(seat_number=seat_number, ticket_id=ticket.id, status='booked', booking_ticket_id=booking_ticket.id)
                db.session.add(new_seat)

        db.session.commit()

        # Thêm thông tin thanh toán
        thanh_toan = Payment(
            booking_id=booking.id,
            amount=amount,
            payment_method='Tại quầy',
            payment_date=datetime.utcnow()
        )
        db.session.add(thanh_toan)
        db.session.commit()

        flash('Bán vé và thanh toán thành công.')
        return redirect(url_for('ban_ve_routes.thong_tin_ve', booking_id=booking.id))


@ban_ve_routes.route('/xac_nhan_ban_ve/<id>/<schedule_flight_id>', methods=['POST'])
def xac_nhan_ban_ve(id, schedule_flight_id):
    # Lấy thông tin từ form
    seat_numbers = request.form.getlist('seat_numbers')
    seat_numbers = [seat for seat in seat_numbers if seat]
    role = session.get('user', {}).get('role', 'Customer')
    username = session['user']['username']

    # Kiểm tra xem người dùng đã chọn ghế chưa
    if not seat_numbers:
        flash('Vui lòng chọn chỗ ngồi trước khi xác nhận.', 'error')
        return redirect(url_for('ban_ve_routes.ban_ve', id=id, schedule_flight_id=schedule_flight_id))

    # Lấy thông tin vé và lịch trình chuyến bay
    ticket_flight = Ticket.query.filter_by(id=id).first()
    schedule_flight = FlightSchedule.query.filter_by(id=schedule_flight_id).first()

    if ticket_flight and schedule_flight:
        # Kiểm tra xem từng ghế đã được đặt chưa
        for seat_number in seat_numbers:
            existing_seat = Seat.query.filter_by(seat_number=seat_number, ticket_id=id).first()
            if existing_seat:
                flash(f'Ghế {seat_number} đã được đặt. Vui lòng chọn ghế khác.', 'error')
                return redirect(url_for('ban_ve_routes.ban_ve', id=id, schedule_flight_id=schedule_flight_id))

        booked_seats = db.session.query(func.sum(BookingTicket.quantity)) \
                    .join(Ticket, BookingTicket.ticket_id == Ticket.id) \
                    .join(Booking, BookingTicket.booking_id == Booking.id) \
                    .filter(Booking.flight_schedule_id == schedule_flight_id,
                            Ticket.ticket_class == ticket_flight.ticket_class) \
                    .scalar() or 0

        total_seats = ticket_flight.quantity
        remaining_tickets = total_seats - booked_seats

        # Chuyển hướng đến trang dat_ve.html
        return render_template('ban_ve.html', 
                               ticket_flight=ticket_flight,
                               schedule_flight=schedule_flight,
                               seat_numbers=seat_numbers,
                               role=role,
                               remaining_tickets=remaining_tickets,
                               schedule_flight_id=schedule_flight_id,
                               username=username)
    
    flash('Không tìm thấy thông tin chuyến bay hoặc vé.', 'error')
    return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))


@ban_ve_routes.route('/thong_tin_ve/<booking_id>', methods=['GET'])
def thong_tin_ve(booking_id):
    try:
        username = session['user']['username']
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
                seat_numbers = [seat.seat_number for seat in booking_ticket.seat]
                formatted_seat_numbers = ', '.join(format_seat_number(seat) for seat in seat_numbers)
                if ticket.ticket_class == '1':
                    service_fee = 150000
                else:
                    service_fee = 100000
                total_quantity += booking_ticket.quantity
                ticket_details_html += f"""
                <tr>
                    <td>{ticket.ticket_class}</td>
                    <td>{ "{:,.0f}".format(ticket.price).replace(",", ".")} VNĐ</td>
                    <td>{ "{:,.0f}".format(service_fee).replace(",", ".")} VNĐ</td>
                    <td>{ticket.flight_schedule_id}</td>
                    <td>{booking_ticket.quantity}</td>
                    <td>{formatted_seat_numbers}</td>
                </tr>
                """

            # Lấy tổng số tiền từ bảng Payment
            total_amount = booking.payment.amount if booking.payment else 0

            role = session.get('user', {}).get('role', 'Customer')


            return render_template(
                'thong_tin_ve.html',
                booking_info=booking_info,
                flight_info=flight_info,
                total_quantity=total_quantity,
                total_amount=total_amount,
                ticket_details_html=ticket_details_html,  
                role=role,
                username=username
            )
        else:
            flash('Không tìm thấy thông tin đặt vé.')
            return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))
    except Exception as e:
        flash(f'Đã xảy ra lỗi: {str(e)}')
        return redirect(url_for('ban_ve_routes.danh_sach_ban_ve'))
    
def format_seat_number(seat_number):
    seat_num = int(seat_number)
    prefix = chr(65 + (seat_num - 1) // 4)  # 65 là mã ASCII của 'A'
    return f"{prefix}{seat_number}"


