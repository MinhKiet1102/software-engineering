from flask import Blueprint, render_template, redirect, url_for, flash, session, request
# from db_utils import cursor, db
from extensions import db
from datetime import datetime, timedelta
import vnpay
from models import Ticket, Flight, BookingTicket

ve_chuyen_bay_routes = Blueprint('ve_chuyen_bay_routes', __name__)


@ve_chuyen_bay_routes.route('/ve_chuyen_bay/<flight_id>', methods=['GET'])
def ve_chuyen_bay(flight_id):
    try:
        # Truy vấn danh sách vé chuyến bay theo mã chuyến bay
        ticket_list = Ticket.query.filter_by(flight_id=flight_id).all()
        role = session.get('user', {}).get('role', 'Customer')
        return render_template('ve_chuyen_bay.html', ticket_list=ticket_list, flight_id=flight_id,
                               role=role)
    except Exception as e:
        flash(f'Có lỗi xảy ra: {str(e)}')
        return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))  


@ve_chuyen_bay_routes.route('/sua_ve_chuyen_bay/<id>', methods=['GET', 'POST'])
def sua_ve_chuyen_bay(id):
    if request.method == 'GET':
        try:
            # Truy vấn thông tin vé chuyến bay theo mã vé
            flight_ticket = Ticket.query.filter_by(id=id).first()
            role = session.get('user', {}).get('role', 'Customer')
            if flight_ticket:
                return render_template('sua_ve_chuyen_bay.html', flight_ticket=flight_ticket, role=role)
            else:
                flash('Vé chuyến bay không tồn tại!')
                return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=id))
        except Exception as e:
            flash(f'Có lỗi xảy ra: {str(e)}')
            return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay'))  # Hoặc trang phù hợp trong ứng dụng của bạn

    elif request.method == 'POST':
        try:
            # Lấy thông tin từ form
            class_new = request.form['ticket_class']
            price_new = int(request.form['price'])

            # Truy vấn và cập nhật thông tin vé chuyến bay
            flight_ticket = Ticket.query.filter_by(id=id).first()
            if flight_ticket:
                flight_ticket.ticket_class = class_new
                flight_ticket.price = price_new

                # Lưu thay đổi vào cơ sở dữ liệu
                db.session.commit()

                flash('Cập nhật vé chuyến bay thành công!')
                return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', id=flight_ticket.flight_id))
            else:
                flash('Vé chuyến bay không tồn tại!')
                return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', id=flight_ticket.flight_id))
        except Exception as e:
            # Xử lý lỗi nếu có
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}')
            return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=flight_ticket.flight_id))


@ve_chuyen_bay_routes.route('/them_ve_chuyen_bay/<flight_id>', methods=['GET', 'POST'])
def them_ve_chuyen_bay(flight_id):
    if request.method == 'POST':
        price = request.form['price']
        ticket_class = request.form['ticket_class']
        ticket = Ticket(flight_id=flight_id, price=price, ticket_class=ticket_class)
        db.session.add(ticket)
        db.session.commit()
        return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=flight_id))
    
    return render_template('them_ve.html', flight_id=flight_id)


@ve_chuyen_bay_routes.route('/xoa_ve_chuyen_bay/<int:ticket_id>', methods=['POST'])
def xoa_ve_chuyen_bay(ticket_id):
    # Lấy vé theo ID
    ticket = Ticket.query.get(ticket_id)

    BookingTicket.query.filter_by(ticket_id=ticket_id).delete()

    if ticket:
        db.session.delete(ticket)
        db.session.commit()
        flash('Đã xóa vé thành công!', 'success')
    else:
        flash('Không tìm thấy vé cần xóa.', 'danger')
    
    # Chuyển hướng lại trang danh sách vé chuyến bay
    return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=ticket.flight_id))