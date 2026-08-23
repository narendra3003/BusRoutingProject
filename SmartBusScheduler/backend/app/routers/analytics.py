"""
Docstring for SmartBusScheduler.backend.app.routers.analytics

GET /admin/analytics/delay
GET /admin/analytics/driver-utilization
GET /admin/analytics/bus-utilization
GET /admin/analytics/routes
"""
"""
GET /analytics/dashboard

RESPONSE:
{
  total_trips_today: 42,
  active_drivers: 18,
  active_buses: 12,
  delayed_trips: 5,
  recent_overrides: [
    {
      id: 1,
      trip_id: 10,
      old_driver: "John",
      new_driver: "Mike",
      created_at: "2026-04-03T10:00:00"
    }
  ]
}
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..utils import get_current_user

router = APIRouter()

@router.get("/dashboard")
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # For simplicity, we return static data here.
    # In a real implementation, you would query the database to get these metrics.
    return {
        "total_trips_today": 42,
        "active_drivers": 18,
        "active_buses": 12,
        "delayed_trips": 5,
        "recent_overrides": [
            {
                "id": 1,
                "trip_id": 10,
                "old_driver": "John",
                "new_driver": "Mike",
                "created_at": "2026-04-03T10:00:00"
            }
        ]
    }