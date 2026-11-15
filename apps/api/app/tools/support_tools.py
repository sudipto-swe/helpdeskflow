"""Safe tool implementations with customer identity authentication and deterministic refund policy."""
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from apps.api.app.db.models import Customer, Order, Subscription
from apps.api.app.rag.retriever import HybridRetriever, format_citations


class PolicyViolationError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class SupportTools:
    """Enterprise safe tools for support workflow agent."""

    def __init__(self, db: Session):
        self.db = db
        self.retriever = HybridRetriever(db)

    def search_kb(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Search the Knowledge Base and return relevant chunks with citations."""
        results = self.retriever.retrieve(query, top_k=top_k)
        citations = [r["id"] for r in results]
        return {
            "query": query,
            "citations": citations,
            "results": results,
            "formatted": format_citations(results)
        }

    def verify_customer_identity(
        self,
        customer_id: str,
        phone: Optional[str] = None,
        nid_last4: Optional[str] = None
    ) -> bool:
        """Verify customer identity before returning sensitive account information."""
        customer = self.db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return False

        # If phone or NID is provided, verify against records
        if phone:
            clean_p1 = phone.replace("+880", "").replace("-", "").strip()
            clean_p2 = customer.phone.replace("+880", "").replace("-", "").strip()
            if clean_p1 not in clean_p2 and clean_p2 not in clean_p1:
                return False

        if nid_last4 and customer.nid_last4 != nid_last4.strip():
            return False

        return True

    def get_customer(self, customer_id: str, authenticated: bool = False) -> Dict[str, Any]:
        """Retrieve customer details; requires authentication check."""
        if not authenticated:
            raise AuthenticationError(f"Customer identity for {customer_id} is not verified. Access denied.")

        customer = self.db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return {"error": "Customer not found"}

        return {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "address": customer.address
        }

    def get_billing_status(self, customer_id: str, authenticated: bool = False) -> Dict[str, Any]:
        """Fetch subscription and billing statement."""
        if not authenticated:
            raise AuthenticationError(f"Customer identity for {customer_id} not verified.")

        sub = self.db.query(Subscription).filter(Subscription.customer_id == customer_id).first()
        if not sub:
            return {"error": "No subscription found"}

        return {
            "customer_id": customer_id,
            "package_name": sub.package_name,
            "speed": sub.speed,
            "monthly_fee": sub.monthly_fee,
            "status": sub.status,
            "balance_due": sub.balance_due,
            "last_payment_date": sub.last_payment_date
        }

    def get_order_status(self, order_id: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch e-commerce order status; verifies ownership if customer_id is provided."""
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            return {"error": f"Order {order_id} not found"}

        if customer_id and order.customer_id != customer_id:
            raise AuthenticationError(f"Cross-customer access prohibited: Order {order_id} does not belong to {customer_id}")

        return {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "item": order.item,
            "quantity": order.quantity,
            "total_price": order.total_price,
            "status": order.status,
            "date": order.date,
            "delivered_days_ago": order.delivered_days_ago
        }

    def check_refund_policy(
        self,
        item_type: str,  # 'subscription' or 'order'
        days_since_delivery: Optional[int] = None,
        is_opened: bool = False,
        consecutive_downtime_hours: int = 0
    ) -> Dict[str, Any]:
        """DETERMINISTIC REFUND POLICY FUNCTION.
        The LLM MAY NEVER decide refund eligibility by itself.
        Rules:
        1. Subscriptions: Strictly no cash refunds. Prorated bill adjustment ONLY if downtime > 72 consecutive hours.
        2. E-Commerce orders: Return eligible within 7 days of delivery IF unopened with seals intact.
        """
        if item_type == "subscription":
            if consecutive_downtime_hours >= 72:
                prorated_days = consecutive_downtime_hours // 24
                return {
                    "eligible": True,
                    "refund_type": "credit_note_adjustment",
                    "reason": f"Downtime exceeded 72 consecutive hours ({consecutive_downtime_hours} hrs). Eligible for {prorated_days} days prorated credit adjustment.",
                    "requires_approval": True
                }
            return {
                "eligible": False,
                "refund_type": "none",
                "reason": f"Subscription fees are non-refundable. Outage must exceed 72 consecutive hours (reported: {consecutive_downtime_hours} hrs).",
                "requires_approval": False
            }

        elif item_type == "order":
            if days_since_delivery is None or days_since_delivery > 7:
                return {
                    "eligible": False,
                    "refund_type": "none",
                    "reason": f"Return window expired. Items must be returned within 7 calendar days of delivery (current: {days_since_delivery} days).",
                    "requires_approval": False
                }
            if is_opened:
                return {
                    "eligible": False,
                    "refund_type": "none",
                    "reason": "Return rejected. Items must be unopened in original packaging with seals intact.",
                    "requires_approval": False
                }
            return {
                "eligible": True,
                "refund_type": "original_payment_method",
                "reason": "Eligible for return and refund within 7 days in unopened condition.",
                "requires_approval": True
            }

        return {
            "eligible": False,
            "refund_type": "none",
            "reason": f"Unknown item type '{item_type}'.",
            "requires_approval": True
        }

    def create_followup_task(self, title: str, details: str, department: str = "support") -> Dict[str, Any]:
        """Queue a task for support or field operations."""
        return {
            "status": "created",
            "task_id": f"TASK-{hash(title) % 100000}",
            "title": title,
            "department": department,
            "details": details
        }

    def escalate_to_human(self, ticket_id: str, reason: str, priority: str = "urgent") -> Dict[str, Any]:
        """Trigger immediate human tier-2 supervisor escalation."""
        return {
            "escalated": True,
            "ticket_id": ticket_id,
            "reason": reason,
            "priority": priority,
            "queue": "tier_2_human_supervisors"
        }

    def schedule_callback(self, customer_id: str, phone: str, slot: str) -> Dict[str, Any]:
        """Schedule a phone call with a customer relations manager."""
        return {
            "status": "scheduled",
            "customer_id": customer_id,
            "phone": phone,
            "slot": slot
        }
