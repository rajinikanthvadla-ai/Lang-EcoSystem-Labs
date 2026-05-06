import sys
import os

from langchain_core.tools import tool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from fake_db import (
    check_product_stock,
    get_customer_orders,
    get_order,
    get_return_policy,
    request_return,
)


@tool
def lookup_order(order_id: str) -> str:
    """Look up order status and details by order ID (e.g. ORD-1001)."""
    order = get_order(order_id)
    if not order:
        return f"No order found with ID {order_id}"
    return (
        f"Order {order_id}:\n"
        f"  Items: {', '.join(order['items'])}\n"
        f"  Total: Rs.{order['total']}\n"
        f"  Status: {order['status']}\n"
        f"  Tracking: {order.get('tracking_id', 'N/A')}\n"
        f"  Delivery: {order.get('estimated_delivery', order.get('delivered_on', 'N/A'))}"
    )


@tool
def check_stock(product_name: str) -> str:
    """Check if a product is available in stock."""
    return check_product_stock(product_name)


@tool
def get_policy() -> str:
    """Get the store return and refund policy."""
    return get_return_policy()


@tool
def initiate_return(order_id: str) -> str:
    """Start a return process for a delivered order."""
    return request_return(order_id)


@tool
def list_customer_orders(customer_id: str) -> str:
    """List all orders for a customer by their customer ID (e.g. C001)."""
    orders = get_customer_orders(customer_id)
    if not orders:
        return f"No orders found for customer {customer_id}"
    lines = [f"  {o['order_id']}: {o['status']} - Rs.{o['total']}" for o in orders]
    return "Orders:\n" + "\n".join(lines)


ALL_TOOLS = [lookup_order, check_stock, get_policy, initiate_return, list_customer_orders]
TOOL_MAP = {t.name: t for t in ALL_TOOLS}
