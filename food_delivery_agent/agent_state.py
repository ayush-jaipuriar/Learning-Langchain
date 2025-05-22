from typing import TypedDict, List, Optional, Dict

class AgentState(TypedDict):
    # Add fields here based on requirements
    order_id: Optional[str]
    order_details: Optional[Dict]
    customer_location: Optional[Dict] # e.g., {'latitude': float, 'longitude': float}
    restaurant_location: Optional[Dict] # e.g., {'latitude': float, 'longitude': float}
    available_couriers: List[Dict] # List of courier dicts, e.g., [{'id': str, 'current_location': Dict}]
    assigned_courier: Optional[Dict]
    courier_current_location: Optional[Dict]
    delivery_status: str # e.g., "pending_pickup", "in_transit", "delivered", "failed_pickup", "failed_delivery"
    estimated_pickup_time: Optional[str]
    estimated_delivery_time: Optional[str]
    actual_pickup_time: Optional[str]
    actual_delivery_time: Optional[str]
    traffic_conditions: Optional[str] # e.g., "light", "moderate", "heavy"
    weather_conditions: Optional[str] # e.g., "clear", "rainy", "stormy"
    customer_contacted: bool
    restaurant_contacted: bool
    issue_type: Optional[str] # e.g., "courier_delay", "restaurant_delay", "item_unavailable", "customer_unavailable"
    resolution_attempts: int
    error_message: Optional[str]
    notifications: List[str]
    current_step_details: Optional[str] # To track what the agent is currently doing 