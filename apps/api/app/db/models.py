"""SQLAlchemy Database Models for HelpdeskFlow."""
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from apps.api.app.db.session import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False, index=True)
    email = Column(String(100), nullable=False)
    nid_last4 = Column(String(10), nullable=False)
    address = Column(String(255), nullable=False)
    is_synthetic = Column(Boolean, default=True)

    subscription = relationship("Subscription", back_populates="customer", uselist=False, cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="customer")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False, index=True)
    package_name = Column(String(100), nullable=False)
    speed = Column(String(50), nullable=False)
    monthly_fee = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)  # active, suspended, expired
    balance_due = Column(Float, default=0.0)
    billing_cycle_day = Column(Float, default=1)
    last_payment_date = Column(String(50))

    customer = relationship("Customer", back_populates="subscription")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False, index=True)
    item = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)  # Delivered, Shipped, Processing, Cancelled
    date = Column(String(50), nullable=False)
    delivered_days_ago = Column(Float, nullable=True)

    customer = relationship("Customer", back_populates="orders")


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=True, index=True)
    customer_name = Column(String(100), nullable=True)
    text = Column(Text, nullable=False)
    language = Column(String(20), default="en")
    category = Column(String(50), nullable=True)
    priority = Column(String(20), nullable=True)
    sentiment = Column(String(20), default="neutral")
    status = Column(String(50), default="new")  # new, processing, awaiting_approval, resolved, escalated
    confidence = Column(Float, default=0.0)

    # Workflow and Trace info
    draft_response = Column(Text, nullable=True)
    citations = Column(JSON, nullable=True)
    tool_calls = Column(JSON, nullable=True)
    trace_steps = Column(JSON, nullable=True)
    policy_check_passed = Column(Boolean, default=True)
    approval_required = Column(Boolean, default=False)
    human_approved = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="tickets")


class KBDocument(Base):
    __tablename__ = "kb_documents"

    id = Column(String(50), primary_key=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    tags = Column(JSON, nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # Store vector as JSON list for SQLite compatibility
