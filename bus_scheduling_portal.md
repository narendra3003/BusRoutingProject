# 🚌 Role-Based Bus Scheduling Portal

## 🎯 Goal
A role-based bus scheduling portal that:

- Automates timetables using passenger boarding/alighting density.  
- Minimizes bus count & waiting time.  
- Lets **Admin** override schedules.  
- Lets **Customer** search/view schedules.  
- Notifies **Drivers** of assignments.  
- Allows **Uploader** to input raw observation data.  

---

## 🖥️ Frontend (React + Tailwind on Vercel)

### Pages

#### 1. Login / Role Selection
- Role-based access (Customer, Admin/Uploader, Driver).

#### 2. Customer Portal
- Can see all buses by route number.  
- Search buses (by route/stop).  
- See next/previous bus schedule for selected bus/stop.  
- Simple table of stop → arrival/departure (list or map).  

#### 3. Admin Dashboard
- KPI dashboard (buses used, avg wait time, load).  
- View auto-generated future schedules / past data (date-wise and bus-wise views).  
- Override (delay/advance a trip), add/cancel trips.  
- Form to upload observation CSV or manual entry:  
  - Bus no, route, stop-level boarding/alighting.  
- All kinds of data uploads (must follow specific formats).  

#### 4. Driver Portal
- Shows assigned trips & reporting times.  
- Notifications (e.g., “report at depot 7:15 AM”).  

#### 5. Map View (Optional)
- Show stops in order (static Leaflet map).  
- For customer view only.  

---

## 🗄️ Database Structure (PostgreSQL on Supabase/Neon)

### Tables

#### 1. users
- user_id (PK)  
- role (customer/admin/driver/uploader)  
- name  
- email  
- password_hash  

#### 2. stops
- stop_id (PK)  
- stop_code  
- stop_name  
- stop_lat  
- stop_lon  

#### 3. routes
- route_id (PK)  
- route_short_name  
- route_long_name  
- stops (ARRAY of stop_id) 

#### 4. service
- service_id (PK)  
- driver_id (FK users.user_id)  
- conductor_id (nullable)  
- notes  

#### 5. trips
- trip_id (PK)  
- route_id (FK)  
- service_id (FK)  
- date  

#### 6. stop_times
- id (PK)  
- trip_id (FK)  
- stop_id (FK)  
- arrival_time  
- departure_time  
- boarding_in  
- boarding_out  

#### 7. admin_overrides
- id (PK)  
- trip_id (FK)  
- delta_minutes  
- effective_date  
- reason  

#### 8. observation_data
- id (PK)  
- bus_no  
- route_id (FK)  
- stop_id (FK)  
- boarding_count  
- alighting_count  
- timestamp  

#### 9. bus_data
- bus_id (PK)
- passenger_cap_count

#### 10. Crew_data
- crew_id (PK)
- name
- post (Driver/Conductor)
- experience

---

## ⚙️ Backend (FastAPI)

### Key Endpoints & Response Schemas

#### Customer Endpoints

1. **Get schedules for route or stop (today)**

```http
GET /schedules/{route_id}?stop_id={stop_id}
```

**Response:**

```json
{
  "route_id": 12,
  "date": "2025-09-02",
  "previous_trips": [
    {"trip_id": 101, "arrival_time": "08:00", "departure_time": "08:05", "stop_id": 56, "stop_name": "Central"}
  ],
  "next_trips": [
    {"trip_id": 102, "arrival_time": "09:00", "departure_time": "09:05", "stop_id": 56, "stop_name": "Central"}
  ]
}
```

2. **Get stops for a route**

```http
GET /routes/{route_id}/stops
```

**Response:**

```json
{
  "route_id": 12,
  "stops": [
    {"stop_id": 56, "stop_name": "Central", "lat": 19.123, "lon": 72.835},
    {"stop_id": 57, "stop_name": "Park", "lat": 19.130, "lon": 72.840}
  ]
}
```

#### Uploader Endpoints

3. **Upload passenger density and bus data**

```http
POST /observations/upload
```

**Request:**

```json
{
  "bus_no": "MH01AB1234",
  "route_id": 12,
  "stop_id": 56,
  "boarding_count": 12,
  "alighting_count": 5,
  "timestamp": "2025-09-02T07:30:00"
}
```

**Response:**

```json
{"status": "success", "message": "Observation uploaded"}
```

4. **Trigger automated schedule plan**

```http
POST /schedules/optimize
```

**Request:**

```json
{"route_id": 12, "date": "2025-09-02"}
```

**Response:**

```json
{
  "route_id": 12,
  "date": "2025-09-02",
  "optimized_trips": [
    {"trip_id": 223, "start_time": "07:00", "end_time": "07:45", "bus_count": 3}
  ]
}
```

#### Admin Endpoints

5. **Schedule overrides**

```http
POST /schedules/override
```

**Request:**

```json
{"trip_id": 1234, "delta_minutes": -10, "date": "2025-09-02", "reason": "Traffic jam"}
```

**Response:**

```json
{"status": "success", "message": "Override applied"}
```

6. **Admin view past/future trips**

```http
GET /admin/schedules?route_id=12&date=2025-09-02
```

**Response:**

```json
{
  "route_id": 12,
  "date": "2025-09-02",
  "trips": [
    {"trip_id": 201, "start_time": "06:00", "end_time": "06:40"},
    {"trip_id": 202, "start_time": "07:00", "end_time": "07:45"}
  ]
}
```

7. **KPI calculations**

```http
GET /admin/kpis?date=2025-09-02
```

**Response:**

```json
{
  "date": "2025-09-02",
  "avg_wait_time": 5.3,
  "buses_used": 12,
  "load_factor": 0.82
}
```

#### Driver Endpoints

8. **Get driver trips**

```http
GET /drivers/{driver_id}/trips?date=2025-09-02
```

**Response:**

```json
{
  "driver_id": 45,
  "date": "2025-09-02",
  "assigned_trips": [
    {"trip_id": 1234, "report_time": "06:30", "route_id": 12}
  ]
}
```

#### Map Endpoints

9. **Map view of stops for a route**

```http
GET /routes/{route_id}/map
```

**Response:**

```json
{
  "route_id": 12,
  "stops": [
    {"stop_id": 56, "stop_name": "Central", "lat": 19.123, "lon": 72.835},
    {"stop_id": 57, "stop_name": "Park", "lat": 19.130, "lon": 72.840}
  ]
}
```

---

## ✅ Final Tech Stack
- **Frontend:** React + Tailwind (Vercel)  
- **Backend:** FastAPI + SQLAlchemy + Pydantic (Render/Railway)  
- **Database:** PostgreSQL (Supabase/Neon)  
- **Optimization:** OR-Tools (bus scheduling)  
- **Auth:** JWT role-based  
- **Visualization:** Recharts/ECharts + Leaflet (optional)  
- **Deployment:** Vercel (frontend), Render/Railway (backend), Supabase/Neon (DB)  

