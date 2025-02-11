from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta, date
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email
from apscheduler.schedulers import SchedulerAlreadyRunningError
from sqlalchemy import text

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Load secret key from .env file

# Configure database URI and engine options
if os.getenv('SUPABASE_DB_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SUPABASE_DB_URL')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'sslmode': 'verify-full',
            'sslcert': None,
            'sslkey': None,
            'sslrootcert': '/etc/ssl/certs/ca-certificates.crt'
        },
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 5,
        'pool_timeout': 30
    }
else:
    # Local development configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'orders.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define Client model
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Relationship with orders
    orders = db.relationship('Order', backref='client', lazy=True)

# Define Order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    order_date = db.Column(db.Date, nullable=False)  # delivery/collection date
    communication_channel = db.Column(db.String(20), nullable=False)  # 'email' or 'whatsapp'
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    message_sent = db.Column(db.Boolean, default=False, nullable=False)
    message_scheduled_date = db.Column(db.DateTime)
    message_template_id = db.Column(db.Integer, db.ForeignKey('message_template.id'), nullable=True)
    
    # Order details
    details = db.Column(db.Text)  # Detailed description of the order
    delivery_required = db.Column(db.Boolean, default=False)
    delivery_address = db.Column(db.Text)
    delivery_instructions = db.Column(db.Text)
    
    def __repr__(self):
        return f"<Order {self.order_number}>"

# Define Todo model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    
    # Time scheduling fields (all optional)
    week_number = db.Column(db.Integer)  # Week number of the year
    day_of_week = db.Column(db.String(10))  # Monday, Tuesday, etc.
    time_of_day = db.Column(db.Time)  # Specific time
    
    def __repr__(self):
        return f'<Todo {self.title}>'

# Define MessageTemplate model
class MessageTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MessageTemplate {self.name}>'

# Create tables within app context
with app.app_context():
    db.create_all()

# Simple login check. For MVP, we use hard-coded credentials
USERNAME = 'admin'
PASSWORD = 'password'

class OrderForm(FlaskForm):
    customer_name = StringField('Customer Name', validators=[DataRequired()])
    telephone = StringField('Telephone', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    order_date = DateField('Order Date', validators=[DataRequired()])
    communication_channel = SelectField('Preferred Communication', 
                                     choices=[('email', 'Email'), ('whatsapp', 'WhatsApp')],
                                     validators=[DataRequired()])
    details = TextAreaField('Order Details', validators=[DataRequired()],
                          description="Enter all cake details including: type, size, flavor, filling, decorations, and any dietary requirements")
    delivery_required = BooleanField('Delivery Required')
    delivery_address = TextAreaField('Delivery Address')
    delivery_instructions = TextAreaField('Delivery Instructions')

@app.route('/')
def index():
    return redirect(url_for('calendar'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == USERNAME and password == PASSWORD:
            session['user'] = username
            return redirect(url_for('calendar'))
        else:
            flash('Invalid credentials. Please try again.')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# Dashboard showing a list of orders and basic reporting
@app.route('/calendar')
def calendar():
    orders = Order.query.order_by(Order.order_date).all()
    return render_template('dashboard.html', orders=orders)

@app.route('/clients')
def clients():
    clients = Client.query.order_by(Client.name).all()
    return render_template('clients.html', clients=clients)

@app.route('/client/add', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        client = Client(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form.get('phone', ''),
            address=request.form.get('address', ''),
            notes=request.form.get('notes', '')
        )
        db.session.add(client)
        db.session.commit()
        return redirect(url_for('clients'))
    return render_template('add_client.html')

@app.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        client.name = request.form['name']
        client.email = request.form['email']
        client.phone = request.form.get('phone', '')
        client.address = request.form.get('address', '')
        client.notes = request.form.get('notes', '')
        db.session.commit()
        return redirect(url_for('clients'))
    return render_template('edit_client.html', client=client)

@app.route('/messages')
def messages():
    templates = MessageTemplate.query.order_by(MessageTemplate.created_at.desc()).all()
    scheduled_messages = Order.query.filter(
        Order.message_scheduled_date.isnot(None),
        Order.message_sent == False
    ).order_by(Order.message_scheduled_date).all()
    return render_template('messages.html', templates=templates, scheduled_messages=scheduled_messages)

@app.route('/messages/templates/add', methods=['GET', 'POST'])
def add_template():
    if request.method == 'POST':
        template = MessageTemplate(
            name=request.form.get('name'),
            subject=request.form.get('subject'),
            body=request.form.get('body')
        )
        db.session.add(template)
        db.session.commit()
        flash('Message template added successfully!')
        return redirect(url_for('messages'))
    return render_template('add_template.html')

@app.route('/messages/templates/<int:template_id>/edit', methods=['GET', 'POST'])
def edit_template(template_id):
    template = MessageTemplate.query.get_or_404(template_id)
    if request.method == 'POST':
        template.name = request.form.get('name')
        template.subject = request.form.get('subject')
        template.body = request.form.get('body')
        db.session.commit()
        flash('Message template updated successfully!')
        return redirect(url_for('messages'))
    return render_template('edit_template.html', template=template)

@app.route('/messages/templates/<int:template_id>/delete', methods=['POST'])
def delete_template(template_id):
    template = MessageTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    flash('Message template deleted successfully!')
    return redirect(url_for('messages'))

@app.route('/messages/preview', methods=['POST'])
def preview_message():
    template_id = request.form.get('template_id')
    order_id = request.form.get('order_id')
    
    template = MessageTemplate.query.get_or_404(template_id)
    order = Order.query.get_or_404(order_id)
    
    # Replace placeholders with actual order data
    subject = template.subject.replace('{order_number}', order.order_number)
    subject = subject.replace('{customer_name}', order.customer_name)
    
    body = template.body.replace('{order_number}', order.order_number)
    body = body.replace('{customer_name}', order.customer_name)
    body = body.replace('{order_date}', order.order_date.strftime('%Y-%m-%d'))
    
    return jsonify({
        'subject': subject,
        'body': body
    })

@app.route('/settings')
def settings():
    return render_template('settings.html')

# Edit Order
@app.route('/orders/<int:order_id>/edit', methods=['GET', 'POST'])
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    form = OrderForm(obj=order)
    
    if form.validate_on_submit():
        form.populate_obj(order)
        db.session.commit()
        flash('Order updated successfully!', 'success')
        return redirect(url_for('orders'))
    
    return render_template('edit_order.html', form=form, order=order)

# Delete Order
@app.route('/orders/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted successfully!', 'success')
    return redirect(url_for('orders'))

# Add Todo
@app.route('/todos')
def todos():
    todos = Todo.query.order_by(Todo.created_at.desc()).all()
    return render_template('todos.html', todos=todos)

@app.route('/todos/add', methods=['GET', 'POST'])
def add_todo():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        week_number = request.form.get('week_number')
        day_of_week = request.form.get('day_of_week')
        time_of_day = request.form.get('time_of_day')
        
        todo = Todo(
            title=title,
            description=description,
            week_number=int(week_number) if week_number else None,
            day_of_week=day_of_week if day_of_week else None,
            time_of_day=datetime.strptime(time_of_day, '%H:%M').time() if time_of_day else None
        )
        
        db.session.add(todo)
        db.session.commit()
        flash('Todo added successfully!')
        return redirect(url_for('todos'))
        
    return render_template('add_todo.html')

@app.route('/todos/<int:todo_id>/toggle', methods=['POST'])
def toggle_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.completed = not todo.completed
    db.session.commit()
    return jsonify({'success': True, 'completed': todo.completed})

@app.route('/todos/<int:todo_id>/delete', methods=['POST'])
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    flash('Todo deleted successfully!')
    return redirect(url_for('todos'))

# Orders
@app.route('/orders')
def orders():
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/orders/create', methods=['GET', 'POST'])
def create_order():
    form = OrderForm()
    clients = Client.query.order_by(Client.name).all()

    if form.validate_on_submit():
        order = Order(
            order_number=generate_order_number(),
            customer_name=form.customer_name.data,
            telephone=form.telephone.data,
            email=form.email.data,
            order_date=form.order_date.data,
            communication_channel=form.communication_channel.data,
            details=form.details.data,
            delivery_required=form.delivery_required.data,
            delivery_address=form.delivery_address.data,
            delivery_instructions=form.delivery_instructions.data,
            client_id=request.form.get('client_id')  # Get client_id from form
        )
        db.session.add(order)
        db.session.commit()
        flash('Order created successfully!', 'success')
        return redirect(url_for('orders'))
    return render_template('create_order.html', form=form, clients=clients)

def generate_order_number():
    """Generate a unique order number in the format TSE-YYYY-XXX"""
    year = datetime.now().year
    # Get the last order number for this year
    last_order = Order.query.filter(
        Order.order_number.like(f'TSE-{year}-%')
    ).order_by(Order.order_number.desc()).first()
    
    if last_order:
        # Extract the sequence number and increment
        seq = int(last_order.order_number.split('-')[-1]) + 1
    else:
        seq = 1
    
    return f'TSE-{year}-{seq:03d}'

# Stub functions to simulate sending messages

def send_email_review_request(order):
    # Here, integrate with an email API like SendGrid
    print(f"Sending email to {order.email} for order {order.order_number}")


def send_whatsapp_review_request(order):
    # Here, integrate with WhatsApp Business API
    print(f"Sending WhatsApp message to {order.telephone} for order {order.order_number}")

def send_message(order):
    """Send review request message based on communication channel"""
    try:
        if order.communication_channel == 'email':
            send_email_review_request(order)
        elif order.communication_channel == 'whatsapp':
            send_whatsapp_review_request(order)
        return True
    except Exception as e:
        app.logger.error(f"Error sending message for order {order.id}: {str(e)}")
        return False

# Scheduled job to trigger review requests

def check_and_send_review_requests():
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                # Calculate threshold date
                threshold_date = datetime.utcnow().date() - timedelta(days=1)
                
                # Explicit transaction block
                with connection.begin():
                    # Get pending orders
                    orders = connection.execute(
                        text("""
                            SELECT * FROM "order"
                            WHERE order_date <= :threshold
                            AND message_sent = false
                        """),
                        {'threshold': threshold_date}
                    ).fetchall()

                    # Process orders
                    for order in orders:
                        # Implement message sending logic here
                        send_message(order)
                        
                        # Mark as sent
                        connection.execute(
                            text("""
                                UPDATE "order"
                                SET message_sent = true
                                WHERE id = :order_id
                            """),
                            {'order_id': order.id}
                        )
                    
                    app.logger.info(f"Processed {len(orders)} review requests")

        except Exception as e:
            app.logger.error(f"Job failed: {str(e)}", exc_info=True)

# Add scheduled job
from apscheduler.schedulers import SchedulerAlreadyRunningError
scheduler = BackgroundScheduler()
try:
    scheduler.add_job(
        id='review_requests',
        func=check_and_send_review_requests,
        trigger='interval',
        days=1,
        max_instances=1,
        coalesce=True,
        replace_existing=True
    )
    scheduler.start()
except SchedulerAlreadyRunningError:
    pass

def schedule_order_messages():
    """
    Check for orders that need messages scheduled and schedule them
    This should be run periodically (e.g., daily)
    """
    with app.app_context():
        # Find orders without scheduled messages
        orders = Order.query.filter(
            Order.message_scheduled_date.is_(None),
            Order.message_sent == False
        ).all()
        
        for order in orders:
            # Schedule message for 2 days after order date
            message_date = order.order_date + timedelta(days=2)
            order.message_scheduled_date = message_date
            
        db.session.commit()

@app.route('/events')
def events():
    # Get all orders
    orders = Order.query.all()
    order_events = [{
        'title': order.order_number,
        'start': order.order_date.isoformat(),
        'backgroundColor': '#AED9E0',  # baby blue
        'borderColor': '#AED9E0',
        'extendedProps': {
            'type': 'order',
            'customerName': order.customer_name,
            'telephone': order.telephone,
            'email': order.email,
            'details': order.details,
            'deliveryRequired': order.delivery_required,
            'deliveryAddress': order.delivery_address,
            'deliveryInstructions': order.delivery_instructions
        }
    } for order in orders]

    # Get all todos with datetime
    todos = Todo.query.filter(
        Todo.week_number.isnot(None),
        Todo.day_of_week.isnot(None),
        Todo.time_of_day.isnot(None)
    ).all()

    # Convert todos to events
    todo_events = []
    for todo in todos:
        # Calculate the date for this todo based on week number and day of week
        year = datetime.now().y