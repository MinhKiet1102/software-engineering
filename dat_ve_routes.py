from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from db_utils import authenticate_user
from extensions import db
from datetime import datetime, timedelta
from vnpay import vnpay
from models import Airport, Flight, FlightSchedule, Ticket, Rule, Payment, Booking, BookingTicket,User
from sqlalchemy import func, case
from sqlalchemy.orm import aliased

dat_ve_routes = Blueprint('dat_ve_routes', __name__)
AirportStart = aliased(Airport)
AirportDest = aliased(Airport)


@dat_ve_routes.route('/danh_sach_dat_ve', methods=['GET'])
def danh_sach_dat_ve():
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
    FlightSchedule.id.label('flight_schedule_id'),
    (
        case(
            (Ticket.ticket_class == 'Hạng 1', FlightSchedule.quantity_class1),
            (Ticket.ticket_class == 'Hạng 2', FlightSchedule.quantity_class2),
            else_=0
        ) - func.coalesce(func.sum(BookingTicket.quantity), 0)
    ).label('remaining_tickets')
).join(
    AirportStart, Flight.start_location_id == AirportStart.abbreviate_name  # Join sân bay khởi hành
).join(
    AirportDest, Flight.destination_id == AirportDest.abbreviate_name  # Join sân bay đến
).join(
    FlightSchedule, Flight.id == FlightSchedule.flight_id
).join(
    Ticket, Flight.id == Ticket.flight_id
).outerjoin(  # Outer join để tính tổng số lượng vé đã đặt
    BookingTicket, BookingTicket.ticket_id == Ticket.id
).group_by(  # Nhóm theo các trường cần thiết
    Flight.id, AirportStart.name, AirportDest.name,
    FlightSchedule.start_date, Ticket.price, Ticket.id,
    Ticket.ticket_class, FlightSchedule.id,
    FlightSchedule.quantity_class1, FlightSchedule.quantity_class2
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

            # In log kiểm tra
            print(f"Ngay bat dau: {ngay_bat_dau}, Ngay ket thuc: {ngay_ket_thuc}")

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
    )


@dat_ve_routes.route('/vnpay_payment', methods=['POST'])
def vnpay_payment():
    if request.method == 'POST':
        # Lấy thông tin từ form
         # Lấy customer_id từ session
        customer_id = session.get('user', {}).get('id')  # Lấy id người dùng từ session
        if not customer_id:
            flash('Bạn cần đăng nhập để thực hiện thanh toán.', 'error')
            return redirect(url_for('auth.login'))  
        id_post = request.form['id']
        schedule_flight_id = request.form['schedule_flight_id']
        fullname = request.form['fullname']
        identity_card = request.form['identity_card']
        phone_number = request.form['phone_number']
        method = request.form['method']
        order_type = request.form.get('order_type')
        quantity = int(request.form.get('quantity', 1))
        amount = float(request.form.get('amount', 0))  # Lấy dữ liệu dạng float
        amount_in_vnpay = int(amount * 100)  # Chuyển đổi sang số nguyên, nhân với 100
        order_desc = request.form.get('order_desc')
        bank_code = request.form.get('bank_code')
        language = request.form.get('language')

        # Lấy thông tin vé, lịch chuyến bay và quy định
        ticket_flight = Ticket.query.filter_by(id=id_post).first()
        schedule_flight = FlightSchedule.query.filter_by(id=schedule_flight_id).first()
        rule = Rule.query.first()


        if ticket_flight is None and schedule_flight is None and rule is None:
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
                    .filter(Booking.flight_schedule_id == schedule_flight_id, Ticket.ticket_class == 'Hạng 1')\
                    .scalar() or 0  # Trả về 0 nếu không có vé nào được đặt

        booked_seats_class_2 = db.session.query(func.sum(BookingTicket.quantity))\
                    .join(Ticket, BookingTicket.ticket_id == Ticket.id)\
                    .join(Booking, BookingTicket.booking_id == Booking.id)\
                    .filter(Booking.flight_schedule_id == schedule_flight_id, Ticket.ticket_class == 'Hạng 2')\
                    .scalar() or 0

        if ticket_flight.ticket_class == 'Hạng 1' and booked_seats_class_1 >= schedule_flight.quantity_class1:
            flash('Không thể đặt vé do hết chỗ ở hạng 1.', 'error')
            return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))

        if ticket_flight.ticket_class == 'Hạng 2' and booked_seats_class_2 >= schedule_flight.quantity_class2:
            flash('Không thể đặt vé do hết chỗ ở hạng 2.', 'error')
            return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))

        user = User.query.filter_by(id=customer_id).first()
        if not user:
            flash('Thông tin tài khoản không hợp lệ. Vui lòng đăng nhập lại.', 'error')
            return redirect(url_for('auth.login'))
        


        # Tạo đơn đặt vé
        booking = Booking(
            fullname=fullname,  # Sửa "fullname" thành "fullname" theo tên cột trong model
            identity_card=identity_card,  # Sửa "identity_card" thành "identity_card"
            phone_number=phone_number,  # Sửa "phone_number" thành "phone_number"
            customer_id=customer_id,  # Thay bằng thông tin khách hàng liên quan
            flight_schedule_id=schedule_flight_id  # Sửa "schedule_flight_id" thành "flight_schedule_id"
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
    vnp_Amount = float(request.args.get('vnp_Amount'))
    vnp_ResponseCode = request.args.get('vnp_ResponseCode')

    if vnp_ResponseCode == '00':
        try:
            id = vnp_TxnRef.split("-")[0]
            dat_ve = Booking.query.filter(Booking.id == id).first()
            booking_id = dat_ve.id
            if dat_ve:
                thanh_toan = Payment.query.filter(Payment.booking_id == booking_id).first()
                if thanh_toan:
                    thanh_toan.trang_thai = 'Thành công'
                    db.session.commit()
                    flash('Cập nhật trạng thái thanh toán thành công.')
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

    role = session.get('user', {}).get('role', 'Customer')
    return render_template('vnpay_return.html', transaction_no=vnp_TransactionNo, txn_ref=vnp_TxnRef,
                           amount=vnp_Amount, response_code=vnp_ResponseCode, role=role)



@dat_ve_routes.route('/dat_ve/<id>/<schedule_flight_id>', methods=['GET', 'POST'])
def dat_ve(id, schedule_flight_id):
    role = session.get('user', {}).get('role', 'Customer')

    if request.method == 'GET':
        ticket_flight = Ticket.query.filter_by(id=id).first()
        schedule_flight = FlightSchedule.query.filter_by(id=schedule_flight_id).first()
        rule = Rule.query.first()
        booking = Booking.query.filter_by(flight_schedule_id=schedule_flight_id).first()

        if ticket_flight and schedule_flight and rule:
            # Tính thời gian giới hạn đặt vé
            time_buy = schedule_flight.start_date - timedelta(hours=rule.time_buy)

            if datetime.now() < time_buy:
                # Tính số ghế đã đặt
                booked_seats = db.session.query(func.sum(BookingTicket.quantity))\
                    .join(Ticket, BookingTicket.ticket_id == Ticket.id)\
                    .join(Booking, BookingTicket.booking_id == Booking.id)\
                    .filter(Booking.flight_schedule_id == schedule_flight_id,
                            Ticket.ticket_class == ticket_flight.ticket_class)\
                    .scalar() or 0  # Trả về 0 nếu không có vé nào được đặt

                # Số ghế ban đầu dựa vào hạng vé
                if ticket_flight.ticket_class == 'Hạng 1':
                    total_seats = schedule_flight.quantity_class1
                elif ticket_flight.ticket_class == 'Hạng 2':
                    total_seats = schedule_flight.quantity_class2
                else:
                    total_seats = 0

                # Tính số ghế còn lại
                remaining_tickets = total_seats - booked_seats

                # Kiểm tra số ghế còn lại
                if remaining_tickets > 0:
                    return render_template('dat_ve.html', 
                                           ticket_flight=ticket_flight,
                                           schedule_flight_id=schedule_flight_id, 
                                           role=role, 
                                           booking=booking, 
                                           remaining_tickets=remaining_tickets)
                else:
                    flash('Chuyến bay này đã hết vé.')
                    return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))
            else:
                flash('Không thể đặt vé cho chuyến bay này do đã quá thời gian đặt vé.')
                return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))

        flash('Không tìm thấy thông tin chuyến bay.')
        return redirect(url_for('dat_ve_routes.danh_sach_dat_ve'))


