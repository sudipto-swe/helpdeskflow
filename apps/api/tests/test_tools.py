"""Comprehensive unit and security tests for support tools and deterministic policies."""
import pytest

from apps.api.app.db.models import Customer, Order, Subscription
from apps.api.app.db.session import Base, SessionLocal, engine
from apps.api.app.tools.support_tools import AuthenticationError, SupportTools


@pytest.fixture(scope="module")
def tools_fixture():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Add sample customer, sub, order
    test_cust = Customer(
        customer_id="CUST-SAFE-01",
        name="Tariq Khan",
        phone="+8801711223344",
        email="tariq@example.com",
        nid_last4="4321",
        address="House 10, Road 4, Dhanmondi"
    )
    test_sub = Subscription(
        id="SUB-SAFE-01",
        customer_id="CUST-SAFE-01",
        package_name="Pro Gamer",
        speed="60 Mbps",
        monthly_fee=1800.0,
        status="active",
        balance_due=0.0
    )
    test_order = Order(
        order_id="ORD-SAFE-99",
        customer_id="CUST-SAFE-01",
        item="Cat6 Ethernet Cable (10m)",
        quantity=1.0,
        total_price=250.0,
        status="Delivered",
        date="2026-11-10",
        delivered_days_ago=4.0
    )
    db.merge(test_cust)
    db.merge(test_sub)
    db.merge(test_order)
    db.commit()

    tools = SupportTools(db)
    yield tools, db
    db.close()


def test_customer_identity_verification(tools_fixture):
    tools, _ = tools_fixture
    # Valid phone match
    assert tools.verify_customer_identity("CUST-SAFE-01", phone="+8801711223344") is True
    assert tools.verify_customer_identity("CUST-SAFE-01", phone="01711223344") is True
    # Valid NID match
    assert tools.verify_customer_identity("CUST-SAFE-01", nid_last4="4321") is True
    # Invalid phone/NID
    assert tools.verify_customer_identity("CUST-SAFE-01", phone="01899999999") is False
    assert tools.verify_customer_identity("CUST-SAFE-01", nid_last4="9999") is False


def test_unauthenticated_access_throws(tools_fixture):
    tools, _ = tools_fixture
    # Unauthenticated access must fail
    with pytest.raises(AuthenticationError):
        tools.get_customer("CUST-SAFE-01", authenticated=False)

    with pytest.raises(AuthenticationError):
        tools.get_billing_status("CUST-SAFE-01", authenticated=False)


def test_cross_customer_order_tampering_blocked(tools_fixture):
    tools, _ = tools_fixture
    # Accessing another customer's order must be blocked
    with pytest.raises(AuthenticationError):
        tools.get_order_status("ORD-SAFE-99", customer_id="CUST-DIFFERENT-99")


def test_deterministic_refund_policy_subscription(tools_fixture):
    tools, _ = tools_fixture
    # < 72 hours downtime is ineligible
    res1 = tools.check_refund_policy(item_type="subscription", consecutive_downtime_hours=24)
    assert res1["eligible"] is False
    assert res1["refund_type"] == "none"

    # >= 72 hours downtime is eligible for credit note adjustment
    res2 = tools.check_refund_policy(item_type="subscription", consecutive_downtime_hours=96)
    assert res2["eligible"] is True
    assert res2["refund_type"] == "credit_note_adjustment"
    assert res2["requires_approval"] is True


def test_deterministic_refund_policy_order(tools_fixture):
    tools, _ = tools_fixture
    # Unopened within 7 days -> eligible
    res1 = tools.check_refund_policy(item_type="order", days_since_delivery=3, is_opened=False)
    assert res1["eligible"] is True
    assert res1["refund_type"] == "original_payment_method"

    # Opened package -> ineligible
    res2 = tools.check_refund_policy(item_type="order", days_since_delivery=3, is_opened=True)
    assert res2["eligible"] is False

    # Delivered > 7 days ago -> ineligible
    res3 = tools.check_refund_policy(item_type="order", days_since_delivery=12, is_opened=False)
    assert res3["eligible"] is False
