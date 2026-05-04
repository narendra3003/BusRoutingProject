from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta, time
from collections import defaultdict
from sqlalchemy.exc import IntegrityError
from typing import Any, List, Dict, Set, Tuple
import csv
import io
import math
from ..database import get_db
from ..models import (
    ScheduleTrip,
    Driver,
    Bus,
    Route,
    DriverLeave,
    OBData,
    Template,
    TemplateRecord,
    User,
    LeaveStatus,
    TripStatus,
    BusStatus,
    DriverStatus,
)
from ..schemas import (
    TripCreate,
    TripUpdate,
    TripResponse,
    TemplateConfig,
    ScheduleGenerationRequest as scheduleRequest,
)
from ..utils import get_current_user

router = APIRouter()

# creates schedule using NSGA-II algorithm and also interacts with db to store the generated schedule modularised code for better readability and maintainability
"""
templates are
"""

@router.post("/generate-templates")
def generate_templates(
    payload: TemplateConfig,
    description: str = "Generated from OB data",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    bus_count = payload.bus_count
    driver_count = payload.driver_count

    