from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from authentication_routes import authenticate_user
from extensions import db
from datetime import datetime, timedelta
from vnpay import vnpay
from models import Airport, Flight, FlightSchedule, Ticket, Rule, Payment, Booking, BookingTicket,User, Seat
from sqlalchemy import func, case
from sqlalchemy.orm import aliased
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict
import hashlib


dat_ve_routes = Blueprint('dat_ve_routes', __name__)
SENDER_EMAIL = "aivivu2016@gmail.com"
SENDER_PASSWORD = "foej pojr trve zagc"
AirportStart = aliased(Airport)
AirportDest = aliased(Airport)


@dat_ve_routes.route('/danh_sach_dat_ve', methods=['GET'])
def danh_sach_dat_ve():
    airport_departure_list = db.session.query(Airport).join(Flight, Flight.start_location_id == Airport.abbreviate_name).distinct().all()
    airport_arrival_list = db.session.query(Airport).join(Flight, Flight.destination_id == Airport.abbreviate_name).distinct().all()
    username = session['user']['username']

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
        ) >= db.session.query(Rule.time_buy).scalar()
    )

    flight_list = query.all()

    # Kiểm tra nếu không có chuyến bay nào được tìm thấy
    if not flight_list:
        flash('Không có chuyến bay phù hợp với lịch trình đã chọn. Vui lòng thử chọn lịch trình khác.', 'warning')

    role = session.get('user', {}).get('role', 'Customer')
    return render_template(
        'danh_sach_dat_ve.html',
        airport_departure_list=airport_departure_list,
        airport_arrival_list=airport_arrival_list,
        airport_departure_selected=airport_departure_selected,
        airport_arrival_selected=airport_arrival_selected,
        start_date=start_date,
        flight_list=flight_list,
        role=role,
        username=username
    )

@dat_ve_routes.route('/vnpay_payment', methods=['POST'])
def vnpay_payment():
    if request.method == 'POST':
        # Lấy thông tin từ form
         # Lấy customer_id từ session
        customer_id = session.get('user', {}).get('id')  # Lấy id người dùng từ session
        if not customer_id:
            flash('Bạn cần đăng nhập để thực hiện thanh toán.', 'error')
            return redirect(url_for('authentication_routes.index'))  
        id_post = request.form['id']
        schedule_flight_id = request.form['schedule_flight_id']
        fullname = request.form['fullname']
        identity_card = request.form['identity_card']
        phone_number = request.form['phone_number']
        method = request.form['method']
        order_type = request.form.get('order_type')
        quantity = int(request.form.get('quantity', 1))
        amount_str = request.form.get('amount', '')
        amount_cleaned = amount_str.replace('.', '').replace(' VNĐ', '')
        amount = float(amount_cleaned)  # Lấy dữ liệu dạng float
        amount_in_vnpay = int(amount * 100)  # Chuyển đổi sang số nguyên, nhân với 100
        order_desc = request.form.get('order_desc')
        bank_code = request.form.get('bank_code')
        language = request.form.get('language')
        seat_numbers_str = request.form.get('seat_numbers')  # Lấy chuỗi ghế
        seat_numbers = seat_numbers_str.replace("[", "").replace("]", "").replace("'", "").split(',')

        # Lấy thông tin vé, lịch chuyến bay và quy định
        ticket_flight = Ticket.query.filter_by(id=id_post).first()
        schedule_flight = FlightSchedule.query.filter_by(id=schedule_flight_id).first()
        rule = Rule.query.first()


        if ticket_flight is None or schedule_flight is None or rule is None:
            flash('Thông tin vé hoặc lịch chuyến bay không hợp lệ.', 'error')
            return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))
        # Kiểm tra thời gian đặt vé
        time_buy = schedule_flight.start_date - timedelta(hours=rule.time_buy)
        if datetime.now() > time_buy:
            flash('Không thể đặt vé do đã quá thời gian cho phép.', 'error')
            return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))

         # Tính số ghế đã đặt cho Hạng 1
        booked_seats_class_1 = db.session.query(func.sum(BookingTicket.quantity))\
                    .join(Ticket, BookingTicket.ticket_id == Ticket.id)\
                    .join(Booking, BookingTicket.booking_id == Booking.id)\
                    .filter(Booking.flight_schedule_id == schedule_flight_id, Ticket.ticket_class == '1')\
                    .scalar() or 0  # Trả về 0 nếu không có vé nào được đặt

        booked_seats_class_2 = db.session.query(func.sum(BookingTicket.quantity))\
                    .join(Ticket, BookingTicket.ticket_id == Ticket.id)\
                    .join(Booking, BookingTicket.booking_id == Booking.id)\
                    .filter(Booking.flight_schedule_id == schedule_flight_id, Ticket.ticket_class == '2')\
                    .scalar() or 0

        if ticket_flight.ticket_class == '1' and booked_seats_class_1 >= ticket_flight.quantity:
            flash('Không thể đặt vé do hết chỗ ở hạng 1.', 'error')
            return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))

        if ticket_flight.ticket_class == '2' and booked_seats_class_2 >= ticket_flight.quantity:
            flash('Không thể đặt vé do hết chỗ ở hạng 2.', 'error')
            return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))

        user = User.query.filter_by(id=customer_id).first()
        if not user:
            flash('Thông tin tài khoản không hợp lệ. Vui lòng đăng nhập lại.', 'error')
            return redirect(url_for('auth.login'))
        


        # Tạo đơn đặt vé
        booking = Booking(
            fullname=fullname,  
            identity_card=identity_card,  
            phone_number=phone_number, 
            customer_id=customer_id, 
            flight_schedule_id=schedule_flight_id  
        )
        db.session.add(booking)
        db.session.commit()

        booking_id = booking.id

        booking_ticket = BookingTicket(
            booking_id=booking_id,
            ticket_id=id_post,
            quantity=quantity
        )
        db.session.add(booking_ticket)
        db.session.commit()

         # Lưu thông tin ghế vào cơ sở dữ liệu
        for seat_number in seat_numbers:
            seat_number = seat_number.strip()  # Loại bỏ khoảng trắng
            if seat_number:  # Kiểm tra nếu không rỗng
                new_seat = Seat(seat_number=seat_number, ticket_id=id_post, status='booked', booking_ticket_id=booking_ticket.id)
                db.session.add(new_seat)

        db.session.commit()

        # Tạo thông tin thanh toán
        thanh_toan = Payment(
            booking_id=booking_id,  
            amount=amount,  
            payment_method=method,  
            payment_date=datetime.utcnow(),  
        )

        db.session.add(thanh_toan)
        db.session.commit()

        # Cấu hình VNPay
        vnp = vnpay()
        vnp.requestData['vnp_Version'] = '2.1.0'
        vnp.requestData['vnp_Command'] = 'pay'
        vnp.requestData['vnp_TmnCode'] = 'X66MTG0V'
        vnp.requestData['vnp_Amount'] = amount_in_vnpay
        vnp.requestData['vnp_CurrCode'] = 'VND'
        vnp.requestData['vnp_TxnRef'] = f"{booking_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        vnp.requestData['vnp_OrderInfo'] = order_desc
        vnp.requestData['vnp_OrderType'] = order_type
        vnp.requestData['vnp_Locale'] = language if language else 'vn'
        vnp.requestData['vnp_BankCode'] = bank_code if bank_code else ''
        vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
        vnp.requestData['vnp_IpAddr'] = request.remote_addr
        vnp.requestData['vnp_ReturnUrl'] = url_for('dat_ve_routes.vnpay_return', _external=True)

        # Tạo URL thanh toán
        vnpay_payment_url = vnp.get_payment_url('https://sandbox.vnpayment.vn/paymentv2/vpcpay.html',
                                                'CBOBJWUW1HBHQQESTURDT7AEMJJOFXIR')
        return redirect(vnpay_payment_url)

    flash('Invalid request', 'error')
    return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))


@dat_ve_routes.route('/vnpay_return', methods=['GET'])
def vnpay_return():
    vnp_TransactionNo = request.args.get('vnp_TransactionNo')
    vnp_TxnRef = request.args.get('vnp_TxnRef')
    vnp_Amount = float(request.args.get('vnp_Amount'))/100
    vnp_ResponseCode = request.args.get('vnp_ResponseCode')
    role = session.get('user', {}).get('role', 'Customer')
    username = session['user']['username']  

    if vnp_ResponseCode == '00':
        try:
            id = vnp_TxnRef.split("-")[0]
            dat_ve = Booking.query.filter(Booking.id == id).first()
            flight_schedule = dat_ve.flight_schedule
            booking_id = dat_ve.id
            # Giả sử bảng User có trường email
            user = User.query.filter_by(id=dat_ve.customer_id).first()
            if not user:
                flash('Không tìm thấy thông tin người dùng.', 'error')
                return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))

            recipient_email = user.email
            if dat_ve:
                customer_name = dat_ve.fullname  # Example field
                customer_identity_card = dat_ve.identity_card
                customer_phone = dat_ve.phone_number
                flight = flight_schedule.flight  # Truy cập đối tượng flight
                airport_departure = flight.airport_departure.name
                airport_arrival = flight.airport_arrival.name
                start_date = flight_schedule.start_date.strftime("%d-%m-%Y %H:%M:%S")
                flight_time = flight_schedule.flight_time
                ticket_details_html = ""
                total_quantity = 0
                for booking_ticket in dat_ve.tickets:
                    ticket = booking_ticket.ticket
                    total_quantity += booking_ticket.quantity
                    seat_numbers = [seat.seat_number for seat in booking_ticket.seat]
                    formatted_seat_numbers = ', '.join(format_seat_number(seat) for seat in seat_numbers)
                    if ticket.ticket_class == '1':
                        service_fee = 150000
                    else:
                        service_fee = 100000
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


                thanh_toan = Payment.query.filter(Payment.booking_id == booking_id).first()
                if thanh_toan:
                    thanh_toan.trang_thai = 'Thành công'
                    db.session.commit()
                else:
                    flash('Không tìm thấy thông tin thanh toán.')
                
            else:
                flash('Không tìm thấy thông tin đặt vé.')
        except Exception as e:
            print(f"Error updating database: {str(e)}")
            db.session.rollback()
            flash('Lỗi cập nhật trạng thái thanh toán.')

    else:
        flash('Lỗi thanh toán. Vui lòng thử lại hoặc liên hệ với hỗ trợ.')
        return render_template('vnpay_failure.html', role=role)
    
    try:
        send_booking_confirmation_email(
            recipient_email=recipient_email,
            booking_info=dat_ve,
            flight_info=flight,
            start_date=start_date,
            flight_time=flight_time,
            total_amount="{:,.0f}".format(vnp_Amount).replace(",", "."),
            ticket_details_html=ticket_details_html
        )
        flash('Cập nhật trạng thái thanh toán thành công và Email xác nhận đã được gửi.', 'success')
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        flash('Không thể gửi email xác nhận. Vui lòng kiểm tra lại.', 'error')

    
    return render_template('vnpay_return.html', transaction_no=vnp_TransactionNo, txn_ref=vnp_TxnRef,
                           amount=vnp_Amount, response_code=vnp_ResponseCode,
                            role=role,customer_name=customer_name, customer_identity_card=customer_identity_card,
                            customer_phone=customer_phone, airport_departure=airport_departure,airport_arrival=airport_arrival,
                            start_date=start_date, flight_time=flight_time,total_quantity=total_quantity,
                            ticket_details_html=ticket_details_html, username=username)


@dat_ve_routes.route('/dat_ve/<id>/<schedule_flight_id>', methods=['GET', 'POST'])
def dat_ve(id, schedule_flight_id):
    role = session.get('user', {}).get('role', 'Customer')
    username = session['user']['username']  

    if request.method == 'GET':
        ticket_flight = Ticket.query.filter_by(id=id).first()
        schedule_flight = FlightSchedule.query.filter_by(id=schedule_flight_id).first()
        rule = Rule.query.first()

        if ticket_flight and schedule_flight and rule:
            # Tính thời gian giới hạn đặt vé
            time_buy = schedule_flight.start_date - timedelta(hours=rule.time_buy)

            if datetime.now() < time_buy:
                # Tính tổng số ghế cho từng hạng theo lịch trình
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
                    template = 'dat_cho_hang_1.html' if ticket_flight.ticket_class == '1' else 'dat_cho_hang_2.html'
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
                    return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))
            else:
                flash('Không thể đặt vé cho chuyến bay này do đã quá thời gian đặt vé.')
                return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))

        flash('Không tìm thấy thông tin chuyến bay.')
        return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))
    

    

@dat_ve_routes.route('/xac_nhan_dat_cho/<id>/<schedule_flight_id>', methods=['POST'])
def xac_nhan_dat_cho(id, schedule_flight_id):
    username = session['user']['username']
    # Lấy thông tin từ form
    seat_numbers = request.form.getlist('seat_numbers')
    seat_numbers = [seat for seat in seat_numbers if seat]
    role = session.get('user', {}).get('role', 'Customer')

    # Kiểm tra xem người dùng đã chọn ghế chưa
    if not seat_numbers:
        flash('Vui lòng chọn chỗ ngồi trước khi xác nhận.', 'error')
        return redirect(url_for('dat_ve_routes.dat_ve', id=id, schedule_flight_id=schedule_flight_id))

    # Lấy thông tin vé và lịch trình chuyến bay
    ticket_flight = Ticket.query.filter_by(id=id).first()
    schedule_flight = FlightSchedule.query.filter_by(id=schedule_flight_id).first()

    if ticket_flight and schedule_flight:
        # Kiểm tra xem từng ghế đã được đặt chưa
        for seat_number in seat_numbers:
            existing_seat = Seat.query.filter_by(seat_number=seat_number, ticket_id=id).first()
            if existing_seat:
                flash(f'Ghế {seat_number} đã được đặt. Vui lòng chọn ghế khác.', 'error')
                return redirect(url_for('dat_ve_routes.dat_ve', id=id, schedule_flight_id=schedule_flight_id))

        booked_seats = db.session.query(func.sum(BookingTicket.quantity)) \
                    .join(Ticket, BookingTicket.ticket_id == Ticket.id) \
                    .join(Booking, BookingTicket.booking_id == Booking.id) \
                    .filter(Booking.flight_schedule_id == schedule_flight_id,
                            Ticket.ticket_class == ticket_flight.ticket_class) \
                    .scalar() or 0

        total_seats = ticket_flight.quantity
        remaining_tickets = total_seats - booked_seats

        # Chuyển hướng đến trang dat_ve.html
        return render_template('dat_ve.html', 
                               ticket_flight=ticket_flight,
                               schedule_flight=schedule_flight,
                               seat_numbers=seat_numbers,
                               role=role,
                               remaining_tickets=remaining_tickets,
                               schedule_flight_id=schedule_flight_id,
                               username=username)
    
    flash('Không tìm thấy thông tin chuyến bay hoặc vé.', 'error')
    return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))

@dat_ve_routes.route('/danh_sach_ve_da_dat', methods=['GET'])
def danh_sach_ve_da_dat():
    role = session.get('user', {}).get('role', 'Customer')
    username = session['user']['username']
    user_id = session['user']['id']

    if not user_id:
        return "Vui lòng đăng nhập để xem thông tin đặt vé", 403

    bookings = (
    db.session.query(Booking, Flight, BookingTicket, Ticket, Seat)
    .join(FlightSchedule, Booking.flight_schedule_id == FlightSchedule.id)
    .join(Flight, FlightSchedule.flight_id == Flight.id)
    .join(BookingTicket, Booking.id == BookingTicket.booking_id)
    .join(Ticket, BookingTicket.ticket_id == Ticket.id)
    .join(Seat, BookingTicket.id == Seat.booking_ticket_id)
    .filter(Booking.customer_id == user_id)
    .all()
)

    # Chuẩn bị dữ liệu để hiển thị
    formatted_bookings = defaultdict(lambda: {
        'flight_id': '',
        'flight_route': '',
        'quantity': 0,
        'ticket_class': '',
        'price': 0,
        'booking_date': None,
        'seat_numbers': []
    })

    for booking, flight, booking_ticket, ticket, seat in bookings:
        booking_info = formatted_bookings[booking.id]
        booking_info['flight_id'] = flight.id
        booking_info['flight_route'] = f"{flight.start_location} - {flight.destination}"
        booking_info['quantity'] = booking_ticket.quantity
        booking_info['ticket_class'] = ticket.ticket_class
        booking_info['price'] = (int)(ticket.price) * booking_ticket.quantity
        booking_info['booking_date'] = booking.booking_date
        booking_info['seat_numbers'].append(format_seat_number(seat.seat_number))

    # Chuyển đổi defaultdict thành danh sách
    formatted_bookings_list = [
        {
            'booking_id': booking_id,
            'flight_id': info['flight_id'],
            'flight_route': info['flight_route'],
            'quantity': info['quantity'],
            'ticket_class': info['ticket_class'],
            'price': info['price'],
            'booking_date': info['booking_date'],
            'seat_numbers': ', '.join(info['seat_numbers'])
        }
        for booking_id, info in formatted_bookings.items()
]

    return render_template('danh_sach_ve_da_dat.html', bookings=formatted_bookings_list, username=username, role=role)

def format_seat_number(seat_number):
    seat_num = int(seat_number)
    prefix = chr(65 + (seat_num - 1) // 4)  # 65 là mã ASCII của 'A'
    return f"{prefix}{seat_number}"

def send_booking_confirmation_email(recipient_email, booking_info, flight_info, start_date, flight_time, total_amount, ticket_details_html):
    """Hàm gửi email xác nhận đặt vé thành công"""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = 'Xác nhận đặt vé thành công'

    body = f"""
    <html>
    <body>
    <h1>Thông tin khách hàng</h1>
    <p><strong>Mã đặt vé:</strong> {booking_info.id}</p>
    <p><strong>Họ tên:</strong> {booking_info.fullname}</p>
    <p><strong>CMND/CCCD:</strong> {booking_info.identity_card}</p>
    <p><strong>Số điện thoại:</strong> {booking_info.phone_number}</p>

    <h1>Thông tin chuyến bay</h1>
    <p><strong>Sân bay đi:</strong> {flight_info.airport_departure.name}</p>
    <p><strong>Sân bay đến:</strong> {flight_info.airport_arrival.name}</p>
    <p><strong>Ngày giờ khởi hành:</strong> {start_date}</p>
    <p><strong>Thời gian bay:</strong> {flight_time} phút</p>
    <p><strong>Tổng số tiền thanh toán:</strong> {total_amount} VNĐ</p>

    <h1>Thông tin vé:</h1>
    <table border="1" style="width:100%; text-align:center;">
        <thead>
            <tr>
                <th>Hạng vé</th>
                <th>Giá/1 vé</th>
                <th>Phí dịch vụ/1 vé</th>
                <th>Mã lịch chuyến bay</th>
                <th>Số lượng</th>
                <th>Số ghế</th>
            </tr>
        </thead>
        <tbody>
            {ticket_details_html}
        </tbody>
    </table>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))

    # Gửi email qua SMTP
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
    server.quit()


@dat_ve_routes.route('/profile', methods=['GET', 'POST'])
def profile():
    username = session['user']['username']
    user_id = session.get('user', {}).get('id')  
    role = session.get('user', {}).get('role', 'Customer')
    customer = User.query.filter_by(id=user_id, role='Customer').first()  

    if not customer:
        flash("Không tìm thấy thông tin khách hàng.", "danger")
        return redirect(url_for('authentication_routes.index'))

    if request.method == 'POST':
        if 'change_password' in request.form:  # Xử lý đổi mật khẩu
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            # Kiểm tra dữ liệu
            if not new_password or not confirm_password:
                flash("Vui lòng nhập đầy đủ thông tin mật khẩu.", "warning")
            elif new_password != confirm_password:
                flash("Mật khẩu xác nhận không khớp.", "danger")
            else:
                try:
                    # Mã hóa mật khẩu với MD5
                    hashed_password = hashlib.md5(new_password.encode()).hexdigest()

                    # Cập nhật mật khẩu
                    customer.password = hashed_password
                    db.session.commit()
                    flash("Đổi mật khẩu thành công.", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Lỗi khi đổi mật khẩu: {str(e)}", "danger")
        else:  # Xử lý cập nhật thông tin cá nhân
            username = request.form.get('username')
            fullname = request.form.get('fullname')
            phone_number = request.form.get('phone_number')
            email = request.form.get('email')

            # Kiểm tra dữ liệu và cập nhật
            if fullname and phone_number and email:
                try:
                    customer.username = username
                    customer.fullname = fullname
                    customer.phone_number = phone_number
                    customer.email = email
                    db.session.commit()
                    flash("Cập nhật thông tin thành công.", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Lỗi khi cập nhật thông tin: {str(e)}", "danger")
            else:
                flash("Vui lòng nhập đầy đủ thông tin.", "warning")

    return render_template('profile.html', customer=customer, role=role, username=username)



