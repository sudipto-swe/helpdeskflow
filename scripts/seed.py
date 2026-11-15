"""Database seeding script for HelpdeskFlow.
Loads synthetic customers, orders, subscriptions, and tickets into the DB.
"""
import json
from pathlib import Path

from apps.api.app.db.models import Customer, Order, Subscription, Ticket
from apps.api.app.db.session import Base, SessionLocal, engine

DATA_DIR = Path("synth/data")


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Customers & Orders
        cust_file = DATA_DIR / "customers.json"
        if not cust_file.exists():
            raise FileNotFoundError(f"Missing {cust_file}. Run synth scripts first.")

        with open(cust_file, "r", encoding="utf-8") as f:
            customers_data = json.load(f)

        existing_cust_count = db.query(Customer).count()
        if existing_cust_count == 0:
            for c in customers_data:
                customer = Customer(
                    customer_id=c["customer_id"],
                    name=c["name"],
                    phone=c["phone"],
                    email=c["email"],
                    nid_last4=c["nid_last4"],
                    address=c["address"],
                    is_synthetic=c.get("is_synthetic", True)
                )
                db.add(customer)

                sub = c["subscription"]
                subscription = Subscription(
                    id=f"SUB-{c['customer_id']}",
                    customer_id=c["customer_id"],
                    package_name=sub["package_name"],
                    speed=sub["speed"],
                    monthly_fee=float(sub["monthly_fee"]),
                    status=sub["status"],
                    balance_due=float(sub["balance_due"]),
                    billing_cycle_day=float(sub["billing_cycle_day"]),
                    last_payment_date=sub["last_payment_date"]
                )
                db.add(subscription)

                for ord_data in c.get("orders", []):
                    order = Order(
                        order_id=ord_data["order_id"],
                        customer_id=c["customer_id"],
                        item=ord_data["item"],
                        quantity=float(ord_data["quantity"]),
                        total_price=float(ord_data["total_price"]),
                        status=ord_data["status"],
                        date=ord_data["date"],
                        delivered_days_ago=float(ord_data["delivered_days_ago"]) if ord_data.get("delivered_days_ago") is not None else None
                    )
                    db.add(order)
            db.commit()
            print(f"Seeded {len(customers_data)} customers, subscriptions, and orders.")
        else:
            print(f"Database already contains {existing_cust_count} customers. Skipping customers seed.")

        # 2. Seed Tickets
        ticket_file = DATA_DIR / "tickets.json"
        if ticket_file.exists():
            with open(ticket_file, "r", encoding="utf-8") as f:
                tickets_data = json.load(f)

            existing_ticket_count = db.query(Ticket).count()
            if existing_ticket_count == 0:
                for t in tickets_data:
                    ticket = Ticket(
                        ticket_id=t["ticket_id"],
                        customer_id=t.get("customer_id"),
                        customer_name=t.get("customer_name"),
                        text=t["text"],
                        language=t.get("language", "en"),
                        category=t.get("category"),
                        priority=t.get("priority"),
                        status=t.get("status", "new")
                    )
                    db.add(ticket)
                db.commit()
                print(f"Seeded {len(tickets_data)} initial tickets.")
            else:
                print(f"Database already contains {existing_ticket_count} tickets. Skipping tickets seed.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
