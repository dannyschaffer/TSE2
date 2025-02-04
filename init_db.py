from app import db, app

if __name__ == "__main__":
    with app.app_context():
        # Warning: This will delete all existing data
        db.drop_all()
        db.create_all()
        print("Database has been reinitialized with the latest schema.")
