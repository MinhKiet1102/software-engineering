from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify
# from db_utils import cursor, db
from extensions import db
from datetime import datetime, timedelta
import vnpay
from models import Flight, Ticket, Booking, Rule, BookingTicket, Payment, FlightSchedule, Airport
from sqlalchemy.orm import aliased
from sqlalchemy import extract, func
quy_dinh_routes = Blueprint('quy_dinh_routes', __name__)


@quy_dinh_routes.route('/doanh_thu_theo_thang', methods=['GET', 'POST'])
def doanh_thu_theo_thang():
    if request.method == 'POST':
        month = int(request.form['selected_month'].split("-")[1])
    else:
        role = session.get('user', {}).get('role', 'Customer')
        return render_template('doanh_thu_theo_thang.html', role=role)

    if not month:
        return jsonify({"error": "Tháng không được cung cấp"}), 400

    results = db.session.query(
        Flight.start_location,
        Flight.destination,
        func.sum(Payment.amount).label('total_revenue'),
        func.count(FlightSchedule.id).label('flight_count')
    ).join(FlightSchedule, Flight.id == FlightSchedule.flight_id)\
     .join(Booking, FlightSchedule.id == Booking.flight_schedule_id)\
     .join(Payment, Booking.id == Payment.booking_id)\
     .filter(func.extract('month', Payment.payment_date) == int(month))\
     .group_by(Flight.start_location, Flight.destination)\
     .all()

    total_revenue = sum(row.total_revenue for row in results)
    data = []

    for row in results:
        data.append({
            "route": f"{row.start_location} - {row.destination}",
            "total_revenue": row.total_revenue,
            "flight_count": row.flight_count,
            "percentage": round((row.total_revenue / total_revenue) * 100, 2) if total_revenue > 0 else 0
        })

    # Đánh số thứ tự cho từng hàng trong data
    data_with_index = [{"index": idx + 1, **row} for idx, row in enumerate(data)]

    return render_template(
        "doanh_thu_theo_thang.html",
        month=month,
        total_revenue=total_revenue,
        data=data_with_index
    )

@quy_dinh_routes.route('/thay_doi_quy_dinh', methods=['GET', 'POST'])
def thay_doi_quy_dinh():
    if request.method == 'GET':
            rule = Rule.query.first()  

            role = session.get('user', {}).get('role', 'Customer')
            return render_template('thay_doi_quy_dinh.html', rule=rule, role=role)
    elif request.method == 'POST':
        rule = Rule.query.first()  
        # Lấy thông tin từ form
        quantity_airport = int(request.form['quantity_airport'])
        min_flight_time = int(request.form['min_flight_time'])
        max_intermediate_airport = int(request.form['max_intermediate_airport'])
        min_stop_time = int(request.form['min_stop_time'])
        max_stop_time = int(request.form['max_stop_time'])
        time_buy = int(request.form['time_buy'])
        time_sell = int(request.form['time_sell'])

        # Lấy bản ghi đầu tiên trong bảng quy định
        rule = Rule.query.first()
        if not rule:
            flash('Không tìm thấy quy định để cập nhật!')
            return redirect(url_for('quy_dinh_routes.thay_doi_quy_dinh'))

        # Cập nhật thông tin trong bản ghi quy định
        rule.quantity_airport = quantity_airport
        rule.min_flight_time = min_flight_time
        rule.max_intermediate_airport = max_intermediate_airport
        rule.min_stop_time = min_stop_time
        rule.max_stop_time = max_stop_time
        rule.time_buy = time_buy
        rule.time_sell = time_sell

        # Lưu thay đổi vào cơ sở dữ liệu
        db.session.commit()

        flash('Cập nhật quy định thành công!')
        return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))
    return render_template('thay_doi_quy_dinh.html', rule=rule)


@quy_dinh_routes.route('/bang_thong_ke', methods=['GET', 'POST'])
def bang_thong_ke():
    # Kiểm tra xem yêu cầu là GET hay POST
    if request.method == 'POST':
        selected_month = request.form['selected_month'].split("-")[1]
    else:
        selected_month = request.args.get('selected_month', None)

    # Kiểm tra tính hợp lệ của tháng
    if not selected_month or int(selected_month) < 1 or int(selected_month) > 12:
        return "Vui lòng nhập tháng hợp lệ (1-12)."

    # Truy vấn doanh thu, số lượt bay theo tuyến bay trong tháng
    results = db.session.query(
        Flight.start_location.label('start_location'),       # Mã sân bay khởi hành
        Flight.destination.label('destination'),             # Mã sân bay đến
        db.func.sum(Payment.amount).label('total_revenue'),  # Tổng doanh thu
        db.func.count(FlightSchedule.id).label('total_flights')  # Số lượt bay
    ).join(FlightSchedule, Flight.id == FlightSchedule.flight_id) \
    .join(Booking, FlightSchedule.id == Booking.flight_schedule_id) \
    .join(Payment, Booking.id == Payment.booking_id) \
    .filter(db.extract('month', FlightSchedule.start_date) == selected_month) \
    .group_by(Flight.start_location, Flight.destination) \
    .all()

    # Tính tổng doanh thu
    total_revenue = sum([result.total_revenue for result in results])

    # Tính tỷ lệ doanh thu cho từng tuyến bay
    data = []
    for i, result in enumerate(results, start=1):
        revenue_percentage = (result.total_revenue / total_revenue) * 100 if total_revenue > 0 else 0
        data.append({
            'index': i,
            'route': f"{result.start_location} - {result.destination}",
            'revenue': result.total_revenue,
            'flights': result.total_flights,
            'percentage': revenue_percentage
        })

    # Render template với dữ liệu
    return render_template(
        'bang_thong_ke.html',
        data=data,
        total_revenue=total_revenue,
        selected_month=selected_month
    )
