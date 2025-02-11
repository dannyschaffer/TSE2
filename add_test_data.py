from app import app, db, Client, Order, Todo, MessageTemplate
from datetime import datetime, timedelta

def add_test_data():
    with app.app_context():
        # Add a test message template
        template = MessageTemplate(
            name="Order Confirmation",
            subject="Your Sweet Escape Order #{order_number}",
            body="Dear {customer_name},\n\nThank you for your order #{order_number}. We're excited to create something special for you!"
        )
        db.session.add(template)
        
        # Add a test client
        client = Client(
            name="Jane Smith",
            email="jane.smith@example.com",
            phone="+1234567890",
            address="123 Sweet Street, Bakery Town",
            notes="Prefers chocolate flavors"
        )
        db.session.add(client)
        
        # Add a test order
        order = Order(
            order_number="TSE-2024-001",
            customer_name="Jane Smith",
            telephone="+1234567890",
            email="jane.smith@example.com",
            order_date=datetime.now().date(),
            communication_channel="email",
            client=client,
            
            # Order details
            details="3-tier Wedding Cake (6\", 8\", 10\"). Vanilla with raspberry and white chocolate buttercream. White fondant with silver pearls and fresh flowers. Cascading roses on the side. No nuts.",
            delivery_required=True,
            delivery_address="123 Sweet Street, Bakery Town",
            delivery_instructions="Venue contact: Sarah (Wedding Planner) +1234567890. Delivery by 11 AM."
        )
        db.session.add(order)
        
        # Commit to get IDs
        db.session.commit()
        
        # Update order with template
        order.message_template_id = template.id
        db.session.commit()
        
        # Add some test todos
        todos = [
            Todo(
                title="Prepare ingredients for TSE-2024-001",
                description="Need to buy fresh strawberries and cream",
                week_number=datetime.now().isocalendar()[1],
                day_of_week="Monday",
                time_of_day=datetime.strptime("09:00", "%H:%M").time()
            ),
            Todo(
                title="Design new summer collection",
                description="Create 5 new cake designs for summer",
                week_number=datetime.now().isocalendar()[1],
                day_of_week="Wednesday",
                time_of_day=datetime.strptime("14:00", "%H:%M").time()
            ),
            Todo(
                title="Client Meeting: Wedding Cake Tasting",
                description="Prepare 3 different cake samples for tasting session",
                week_number=datetime.now().isocalendar()[1],
                day_of_week="Friday",
                time_of_day=datetime.strptime("15:30", "%H:%M").time()
            )
        ]
        for todo in todos:
            db.session.add(todo)
        
        # Commit all changes
        db.session.commit()
        print("Test data added successfully!")

if __name__ == "__main__":
    add_test_data()
