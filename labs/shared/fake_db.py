"""
Fake E-Commerce Database
========================
This simulates a real database so students can run everything locally
without needing actual infrastructure. In production, these would be
API calls to your order management system, product catalog, etc.
"""

CUSTOMERS = {
    "C001": {"name": "Rahul Sharma", "email": "rahul@example.com", "tier": "Gold"},
    "C002": {"name": "Priya Patel", "email": "priya@example.com", "tier": "Silver"},
    "C003": {"name": "Amit Kumar", "email": "amit@example.com", "tier": "Bronze"},
}

ORDERS = {
    "ORD-1001": {
        "customer_id": "C001",
        "items": ["Wireless Headphones", "Phone Case"],
        "total": 2499.00,
        "status": "shipped",
        "tracking_id": "TRK-88891",
        "estimated_delivery": "2026-05-10",
    },
    "ORD-1002": {
        "customer_id": "C001",
        "items": ["Laptop Stand"],
        "total": 1899.00,
        "status": "delivered",
        "tracking_id": "TRK-88892",
        "delivered_on": "2026-05-01",
    },
    "ORD-1003": {
        "customer_id": "C002",
        "items": ["USB-C Hub", "Mouse Pad", "Webcam"],
        "total": 4350.00,
        "status": "processing",
        "tracking_id": None,
        "estimated_delivery": "2026-05-15",
    },
    "ORD-1004": {
        "customer_id": "C003",
        "items": ["Mechanical Keyboard"],
        "total": 6999.00,
        "status": "cancelled",
        "tracking_id": None,
        "cancelled_reason": "Customer requested cancellation",
    },
}

PRODUCTS = {
    "P001": {"name": "Wireless Headphones", "price": 1499.00, "stock": 45, "category": "Audio"},
    "P002": {"name": "Phone Case", "price": 999.00, "stock": 120, "category": "Accessories"},
    "P003": {"name": "Laptop Stand", "price": 1899.00, "stock": 0, "category": "Accessories"},
    "P004": {"name": "USB-C Hub", "price": 2199.00, "stock": 30, "category": "Electronics"},
    "P005": {"name": "Mechanical Keyboard", "price": 6999.00, "stock": 15, "category": "Electronics"},
    "P006": {"name": "Webcam", "price": 1599.00, "stock": 60, "category": "Electronics"},
}

RETURN_POLICY = """
Return Policy:
- Items can be returned within 7 days of delivery
- Item must be unused and in original packaging
- Refund is processed within 3-5 business days
- Electronics have a 1-year warranty
- Sale items are final sale (no returns)
"""


# ---------- Helper functions (these simulate real API calls) ----------

def get_order(order_id: str) -> dict | None:
    """Look up an order by ID."""
    return ORDERS.get(order_id)


def get_customer_orders(customer_id: str) -> list[dict]:
    """Get all orders for a customer."""
    return [
        {"order_id": oid, **order}
        for oid, order in ORDERS.items()
        if order["customer_id"] == customer_id
    ]


def get_product(product_id: str) -> dict | None:
    """Look up a product by ID."""
    return PRODUCTS.get(product_id)


def check_product_stock(product_name: str) -> str:
    """Check if a product is in stock by name."""
    for prod in PRODUCTS.values():
        if prod["name"].lower() == product_name.lower():
            if prod["stock"] > 0:
                return f"{prod['name']} is IN STOCK ({prod['stock']} units available) — ₹{prod['price']}"
            return f"{prod['name']} is OUT OF STOCK"
    return f"Product '{product_name}' not found in catalog"


def get_return_policy() -> str:
    """Return the store's return policy."""
    return RETURN_POLICY


def request_return(order_id: str) -> str:
    """Initiate a return request for an order."""
    order = ORDERS.get(order_id)
    if not order:
        return f"Order {order_id} not found"
    if order["status"] != "delivered":
        return f"Cannot return order {order_id} — status is '{order['status']}' (must be 'delivered')"
    return f"✓ Return initiated for {order_id}. Return label sent to customer email. Refund in 3-5 business days."
