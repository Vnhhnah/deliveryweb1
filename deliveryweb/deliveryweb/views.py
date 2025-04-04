from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session, jsonify, g
from deliveryweb import app
import pyodbc  # Thay vì sqlite3, sử dụng pyodbc cho Azure SQL
from flask import Blueprint
from flask import abort
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Thiết lập secret key cho ứng dụng Flask
app.secret_key = os.urandom(24)

# Kết nối đến Azure SQL Database
def get_db():
    if 'db' not in g:
        g.db = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=vgu.database.windows.net;'
            'PORT=1433;'
            'DATABASE=bodoithienha;'
            'UID=quan;'
            'PWD=160303Hang@;'
            'Encrypt=yes;'
            'TrustServerCertificate=no;'
            'Connection Timeout=30;'
        )
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Blueprint cho payment
payments = Blueprint('payments', __name__)

@app.route("/track_order", methods=["GET"])
def track_order():
    order_id = request.args.get("order_id")
    order = None
    if order_id:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cur.fetchone()
    
    return render_template("track_order.html", order=order)

# Trang chủ
@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Trang chủ',
        year=datetime.now().year,
    )

# Trang giới thiệu
@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='Về Chúng Tôi',
        year=datetime.now().year,
        message='Giới thiệu về công ty Transformer và công nghệ giao hàng tự động.'
    )

# Trang liên hệ
@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Liên Hệ',
        year=datetime.now().year,
        message='Liên hệ với chúng tôi để được hỗ trợ nhanh nhất!'
    )

# Đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id, name, email, password FROM users WHERE email = ?", (email,))
        user = cur.fetchone()

        if user and check_password_hash(user[3], password):  # user[3] là mật khẩu đã mã hóa từ cơ sở dữ liệu
            session['user_id'] = user[0]  # Giả sử user[0] là ID người dùng trả về từ SP
            return redirect(url_for('home'))
        else:
            flash('Email hoặc mật khẩu không đúng', 'danger')

    return render_template('login.html')

# Đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cur = db.cursor()
        # Kiểm tra nếu email đã tồn tại qua SP
        cur.execute("{CALL dbo.check_email_exists(?)}", (email,))
        if cur.fetchone()[0] == 1:  # Giả sử trả về 1 nếu email tồn tại
            flash('Email đã tồn tại', 'danger')
        else:
            # Mã hóa mật khẩu trước khi lưu trữ
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            # Thực thi SP đăng ký người dùng
            cur.execute("{CALL dbo.RegisterUser(?, ?, ?)}", (name, email, hashed_password))
            db.commit()
            flash('Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

# Đăng xuất
@app.route('/logout')
def logout():
    """Logs the user out and redirects to home."""
    session.pop('user_id', None)
    flash('Bạn đã đăng xuất.', 'info')
    return redirect(url_for('home'))

# Quản lý đơn hàng
@app.route('/orders')
def orders():
    """Renders the orders page."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM orders")
    orders = cur.fetchall()

    return render_template(
        'orders.html',
        title='Quản lý Đơn Hàng',
        year=datetime.now().year,
        orders=orders  # Thêm danh sách đơn hàng thật từ database
    )

# Xử lý đơn hàng
@app.route('/order/<step>', methods=['GET', 'POST'])
def order_process(step):
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        payment_method = request.form.get('payment_method', '').strip()

        # Kiểm tra nếu bất kỳ thông tin nào bị thiếu
        if not name or not phone or not address or not payment_method:
            flash("Vui lòng nhập đầy đủ thông tin thanh toán.", "danger")
            return redirect(url_for('order_process', step='checkout'))

        if step == 'checkout':
            return redirect(url_for('order_process', step='confirm'))

        flash("Thanh toán thành công! Đơn hàng đang được xử lý.", "success")
        return redirect(url_for('home'))

    return render_template('order_process.html', step=step)

# Quản lý xe tự hành
@app.route('/vehicles')
def vehicles():
    """Renders the vehicles page."""
    return render_template(
        'vehicles.html',
        title='Quản lý Xe Tự Hành',
        year=datetime.now().year
    )

# API kiểm tra trạng thái đơn hàng (để cập nhật trên bản đồ thời gian thực)
@app.route('/api/order_status/<order_id>')
def order_status(order_id):
    """Returns the status of an order (fake API response)."""
    status = {
        "order_id": order_id,
        "status": "Đang giao hàng",
        "location": "Quận 1, TP.HCM"
    }
    return jsonify(status)

@app.route('/oauth_login/<provider>')
def oauth_login(provider):
    return f"OAuth login for {provider} is not implemented yet."

@app.route('/payment_page', methods=['GET', 'POST'])
def payment_page():
    if request.method == 'POST':
        sender_name = request.form['sender_name']
        sender_phone = request.form['sender_phone']
        receiver_name = request.form['receiver_name']
        receiver_phone = request.form['receiver_phone']
        receiver_address = request.form['receiver_address']
        shipping_method = request.form['shipping_method']
        payment_method = request.form['payment_method']
        
        new_order = Order(
            sender_name=sender_name,
            sender_phone=sender_phone,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            receiver_address=receiver_address,
            shipping_method=shipping_method,
            payment_method=payment_method,
            status='pending'
        )
        
        db.session.add(new_order)
        db.session.commit()
        flash('Đơn hàng của bạn đã được xác nhận!', 'success')
        return redirect(url_for('payments.order_success', order_id=new_order.id))
    
    return render_template('checkout.html')

@payments.route('/order_success/<int:order_id>')
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('payments/success.html', order=order)

# API xử lý thanh toán
@payments.route('/process_payment', methods=['POST'])
def process_payment():
    data = request.json

    sender_name = data.get('sender_name')
    sender_phone = data.get('sender_phone')
    receiver_name = data.get('receiver_name')
    receiver_phone = data.get('receiver_phone')
    receiver_address = data.get('receiver_address')
    shipping_method = data.get('shipping_method')
    payment_method = data.get('payment_method')

    if not all([sender_name, sender_phone, receiver_name, receiver_phone, receiver_address, shipping_method, payment_method]):
        return jsonify({'error': 'Thiếu thông tin cần thiết'}), 400

    payment_redirect_urls = {
        'VNPAY': 'https://sandbox.vnpayment.vn/payment',
        'MOMO': 'https://payment.momo.vn/',
        'CREDIT': 'https://secure.creditpayment.com/',
        'PAYPAL': 'https://www.paypal.com/checkout'
    }

    if payment_method in payment_redirect_urls:
        return jsonify({'status': 'success', 'redirect_url': payment_redirect_urls[payment_method]})

    if payment_method == 'COD':
        return jsonify({'status': 'success', 'message': 'Đơn hàng sẽ được thanh toán khi nhận hàng.'})

    if payment_method == 'BANK':
        return jsonify({'status': 'success', 'message': 'Vui lòng thực hiện chuyển khoản theo thông tin được cung cấp.'})

    return jsonify({'error': 'Phương thức thanh toán không hợp lệ'}), 400

# Register the blueprint after defining all routes
app.register_blueprint(payments, url_prefix='/payments')
