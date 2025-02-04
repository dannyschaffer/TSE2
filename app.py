from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
from apscheduler.schedulers.background import BackgroundScheduler
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For demo purposes only. In production, use a secure, random key.

# Configure database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'orders.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
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

# Create database tables
with app.app_context():
    db.create_all()

# Simple login check. For MVP, we use hard-coded credentials
USERNAME = 'admin'
PASSWORD = 'password'

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

# Add Order
@app.route('/orders/add', methods=['GET', 'POST'])
def add_order():
    clients = Client.query.order_by(Client.name).all()
    if request.method == 'POST':
        order_number = request.form.get('order_number')
        customer_name = request.form.get('customer_name')
        telephone = request.form.get('telephone')
        email = request.form.get('email')
        order_date_str = request.form.get('order_date')
        communication_channel = request.form.get('communication_channel')
        
        try:
            order_date = datetime.strptime(order_date_str, '%Y-%m-%d').date()
        except Exception as e:
            flash('Invalid date format. Use YYYY-MM-DD.')
            return redirect(url_for('add_order'))

        # First, try to find an existing client by email or phone
        client = Client.query.filter(
            (Client.email == email) | (Client.phone == telephone)
        ).first()

        # If no existing client found, create a new one
        if not client:
            client = Client(
                name=customer_name,
                email=email,
                phone=telephone
            )
            db.session.add(client)
            db.session.flush()  # This gets us the client.id before committing

        new_order = Order(
            order_number=order_number,
            customer_name=customer_name,
            telephone=telephone,
            email=email,
            order_date=order_date,
            communication_channel=communication_channel,
            client_id=client.id
        )
        db.session.add(new_order)
        
        try:
            db.session.commit()
            flash('Order added successfully.')
        except Exception as e:
            db.session.rollback()
            flash('Error creating order. Please try again.')
            print(f"Error: {str(e)}")
            
        return redirect(url_for('calendar'))
        
    return render_template('add_order.html', clients=clients)

# Edit Order
@app.route('/orders/edit/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    clients = Client.query.order_by(Client.name).all()
    if request.method == 'POST':
        order.order_number = request.form.get('order_number')
        order.customer_name = request.form.get('customer_name')
        order.telephone = request.form.get('tel')
        order.email = request.form.get('email')
        order_date_str = request.form.get('order_date')
        try:
            order.order_date = datetime.strptime(order_date_str, '%Y-%m-%d').date()
        except Exception as e:
            flash('Invalid date format. Use YYYY-MM-DD.')
            return redirect(url_for('edit_order', order_id=order_id))
        order.communication_channel = request.form.get('communication_channel')
        order.client_id = request.form.get('client_id')
        db.session.commit()
        flash('Order updated successfully.')
        return redirect(url_for('calendar'))
    return render_template('edit_order.html', order=order, clients=clients)

# Delete Order
@app.route('/orders/delete/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted successfully.')
    return redirect(url_for('calendar'))

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

# Stub functions to simulate sending messages

def send_email_review_request(order):
    # Here, integrate with an email API like SendGrid
    print(f"Sending email to {order.email} for order {order.order_number}")


def send_whatsapp_review_request(order):
    # Here, integrate with WhatsApp Business API
    print(f"Sending WhatsApp message to {order.telephone} for order {order.order_number}")

# Scheduled job to trigger review requests

def check_and_send_review_requests():
    with app.app_context():
        # Get orders that are 1 day old and haven't had review requests sent
        cutoff_date = date.today() - timedelta(days=1)
        orders_to_process = Order.query.filter(
            Order.order_date <= cutoff_date,
            Order.message_sent == False
        ).all()

        for order in orders_to_process:
            try:
                if order.communication_channel == 'email':
                    send_email_review_request(order)
                elif order.communication_channel == 'whatsapp':
                    send_whatsapp_review_request(order)
                
                order.message_sent = True
                db.session.commit()
            except Exception as e:
                print(f"Error processing order {order.order_number}: {str(e)}")
                db.session.rollback()

# Schedule the review request check
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=check_and_send_review_requests,
    trigger="interval",
    days=1,
    next_run_time=datetime.now() + timedelta(seconds=10),
    id="check_and_send_review_requests"
)

try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()

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
    orders = Order.query.all()
    events = []
    for order in orders:
        events.append({
            'id': order.id,
            'title': f"Order {order.order_number}",
            'start': order.order_date.isoformat()
        })
    return jsonify(events)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
