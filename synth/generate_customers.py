"""Generate 200+ synthetic customers, subscriptions, billing history, and orders.
Fictional company: BengalNet & Bazar (Bangladesh ISP & E-commerce).
All data is strictly synthetic and labeled as such.
"""
import json
import random
from pathlib import Path

random.seed(42)

OUTPUT_DIR = Path("synth/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FIRST_NAMES = [
    "Rahim", "Karim", "Tariq", "Sadia", "Fatima", "Tanvir", "Nusrat", "Anisur", "Fahim",
    "Tasnim", "Rifat", "Sumaiya", "Mahmud", "Ishrat", "Zubair", "Ayesha", "Shakil", "Farhana",
    "Kamrul", "Samia", "Arif", "Mehedi", "Nafisa", "Asif", "Mim", "Hasan", "Sultana", "Imran"
]
LAST_NAMES = [
    "Chowdhury", "Ahmed", "Khan", "Rahman", "Hossain", "Islam", "Haque", "Alam", "Siddique",
    "Ali", "Uddin", "Bhuiyan", "Talukder", "Mahmood", "Sikder", "Akhtar", "Parveen"
]
AREAS = ["Dhanmondi", "Gulshan", "Banani", "Uttara", "Mirpur", "Mohammadpur", "Agrabad", "Zindabazar", "Bashundhara"]
PACKAGES = [
    {"name": "Starter Home", "speed": "15 Mbps", "price": 600},
    {"name": "Family Stream", "speed": "30 Mbps", "price": 1000},
    {"name": "Pro Gamer", "speed": "60 Mbps", "price": 1800},
    {"name": "GigaBiz Enterprise", "speed": "100 Mbps", "price": 3500}
]
ORDER_ITEMS = [
    ("TP-Link Archer C6 Wi-Fi 6 Router", 3200),
    ("D-Link DIR-825 AC1200 Router", 2400),
    ("Cat6 Ethernet Cable (10m)", 250),
    ("Cat6 Ethernet Cable (20m)", 450),
    ("ONU Replacement Optical Unit", 1200),
    ("Mini DC UPS for Wi-Fi Router", 1850),
    ("Fiber Patch Cord SC-UPC 3m", 150)
]


def generate_customers(num_customers: int = 220):
    customers = []
    customer_ids = []

    for i in range(1, num_customers + 1):
        cust_id = f"CUST-{1000 + i}"
        customer_ids.append(cust_id)
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        full_name = f"{first} {last}"
        phone = f"+88017{random.randint(10000000, 99999999)}"
        email = f"{first.lower()}.{last.lower()}{random.randint(10, 99)}@example.com"
        area = random.choice(AREAS)
        nid_last4 = f"{random.randint(1000, 9999)}"

        pkg = random.choice(PACKAGES)
        status = random.choices(["active", "active", "active", "suspended", "expired"], weights=[80, 10, 5, 3, 2])[0]
        balance_due = 0.0 if status == "active" else float(pkg["price"])

        # Generate orders
        num_orders = random.choices([0, 1, 2, 3], weights=[40, 40, 15, 5])[0]
        orders = []
        for o_idx in range(num_orders):
            item, price = random.choice(ORDER_ITEMS)
            qty = random.randint(1, 2)
            total = price * qty
            order_status = random.choice(["Delivered", "Shipped", "Processing", "Cancelled", "Pending"])
            order_id = f"ORD-{20000 + i * 10 + o_idx}"
            orders.append({
                "order_id": order_id,
                "item": item,
                "quantity": qty,
                "total_price": total,
                "status": order_status,
                "date": f"2026-10-{random.randint(1, 28):02d}",
                "delivered_days_ago": random.randint(1, 20) if order_status == "Delivered" else None
            })

        customers.append({
            "customer_id": cust_id,
            "name": full_name,
            "phone": phone,
            "email": email,
            "nid_last4": nid_last4,
            "address": f"House {random.randint(1, 120)}, Road {random.randint(1, 30)}, {area}, Dhaka",
            "subscription": {
                "package_name": pkg["name"],
                "speed": pkg["speed"],
                "monthly_fee": pkg["price"],
                "status": status,
                "balance_due": balance_due,
                "billing_cycle_day": 1,
                "last_payment_date": "2026-11-02" if status == "active" else "2026-09-30"
            },
            "orders": orders,
            "is_synthetic": True
        })

    return customers


def main():
    customers = generate_customers(220)
    out_file = OUTPUT_DIR / "customers.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(customers, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(customers)} synthetic customers at {out_file}")


if __name__ == "__main__":
    main()
