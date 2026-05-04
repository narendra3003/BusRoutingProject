BEGIN;

-- =========================
-- ENUM TYPES
-- =========================

CREATE TYPE user_role AS ENUM ('admin','driver','crew');

CREATE TYPE driver_status AS ENUM ('active','inactive');

CREATE TYPE bus_status AS ENUM ('active','maintenance','inactive');

CREATE TYPE leave_status AS ENUM ('pending','granted','rejected');

CREATE TYPE trip_status AS ENUM ('scheduled','completed','cancelled','delayed');

CREATE TYPE notification_type AS ENUM ('override','leave','system');

CREATE TYPE stop_type AS ENUM ('stop','terminal','depot');

-- =========================
-- STOPS
-- =========================

CREATE TABLE stops (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    type stop_type DEFAULT 'stop',
    zone TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stops_zone ON stops(zone);



-- =========================
-- ROUTES
-- =========================

CREATE TABLE routes (
    id TEXT PRIMARY KEY,   -- example: 101_UP or 101_DOWN
    name TEXT NOT NULL,
    start_stop_id INTEGER NOT NULL,
    end_stop_id INTEGER NOT NULL,
    distance_km NUMERIC(6,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_route_start_stop
        FOREIGN KEY(start_stop_id)
        REFERENCES stops(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_route_end_stop
        FOREIGN KEY(end_stop_id)
        REFERENCES stops(id)
        ON DELETE RESTRICT
);



-- =========================
-- ROUTE STOPS
-- =========================

CREATE TABLE route_stops (
    id SERIAL PRIMARY KEY,

    route_id TEXT NOT NULL,
    stop_id INTEGER NOT NULL,

    seq INTEGER NOT NULL,

    dist_from_start NUMERIC(6,2),
    time_from_start INTEGER, -- minutes from route start

    CONSTRAINT fk_route_stop_route
        FOREIGN KEY(route_id)
        REFERENCES routes(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_route_stop_stop
        FOREIGN KEY(stop_id)
        REFERENCES stops(id)
        ON DELETE RESTRICT,

    CONSTRAINT unique_route_stop_seq
        UNIQUE(route_id, seq),

    CONSTRAINT unique_route_stop
        UNIQUE(route_id, stop_id)
);

CREATE INDEX idx_route_stops_route ON route_stops(route_id);
CREATE INDEX idx_route_stops_stop ON route_stops(stop_id);



-- =========================
-- USERS
-- =========================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,

    email TEXT UNIQUE NOT NULL,
    pass_hash TEXT NOT NULL,

    name TEXT NOT NULL,
    phone TEXT,

    role user_role NOT NULL,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);



-- =========================
-- DRIVERS
-- =========================

CREATE TABLE drivers (

    user_id INTEGER PRIMARY KEY,

    license_no TEXT UNIQUE NOT NULL,

    experience_years INTEGER DEFAULT 0,

    joining_date DATE,

    status driver_status DEFAULT 'active',

    CONSTRAINT fk_driver_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);



-- =========================
-- BUSES
-- =========================

CREATE TABLE buses (

    id SERIAL PRIMARY KEY,

    code TEXT UNIQUE NOT NULL,

    sitting_capacity INTEGER NOT NULL,
    standing_capacity INTEGER DEFAULT 0,

    status bus_status DEFAULT 'active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



-- =========================
-- DRIVER LEAVE
-- =========================

CREATE TABLE driver_leave (

    id SERIAL PRIMARY KEY,

    driver_id INTEGER NOT NULL,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    reason TEXT,

    status leave_status DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_leave_driver
        FOREIGN KEY(driver_id)
        REFERENCES drivers(user_id)
        ON DELETE CASCADE,

    CONSTRAINT valid_leave_dates
        CHECK (end_date >= start_date)
);

CREATE INDEX idx_driver_leave_driver ON driver_leave(driver_id);
CREATE INDEX idx_driver_leave_dates ON driver_leave(start_date,end_date);



-- =========================
-- SCHEDULE TRIPS
-- =========================

CREATE TABLE schedule_trips (

    id SERIAL PRIMARY KEY,

    route_id TEXT NOT NULL,

    trip_date DATE NOT NULL,

    start_time TIME NOT NULL,

    bus_id INTEGER NOT NULL,

    driver_id INTEGER NOT NULL,

    status trip_status DEFAULT 'scheduled',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_trip_route
        FOREIGN KEY(route_id)
        REFERENCES routes(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_trip_bus
        FOREIGN KEY(bus_id)
        REFERENCES buses(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_trip_driver
        FOREIGN KEY(driver_id)
        REFERENCES drivers(user_id)
        ON DELETE RESTRICT,

    CONSTRAINT unique_trip
        UNIQUE(route_id,trip_date,start_time)
);

CREATE INDEX idx_trip_date ON schedule_trips(trip_date);
CREATE INDEX idx_trip_driver_date ON schedule_trips(driver_id,trip_date);
CREATE INDEX idx_trip_bus_date ON schedule_trips(bus_id,trip_date);
CREATE INDEX idx_trip_route_date ON schedule_trips(route_id,trip_date);



-- =========================
-- OVERRIDES (DISPATCH CHANGES)
-- =========================

CREATE TABLE overrides (

    id SERIAL PRIMARY KEY,

    trip_id INTEGER NOT NULL,

    old_driver_id INTEGER,
    new_driver_id INTEGER,

    old_bus_id INTEGER,
    new_bus_id INTEGER,

    reason TEXT,

    created_by INTEGER NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_override_trip
        FOREIGN KEY(trip_id)
        REFERENCES schedule_trips(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_override_user
        FOREIGN KEY(created_by)
        REFERENCES users(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_override_trip ON overrides(trip_id);



-- =========================
-- NOTIFICATIONS
-- =========================

CREATE TABLE notifications (

    id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL,

    title TEXT NOT NULL,

    message TEXT NOT NULL,

    type notification_type DEFAULT 'system',

    is_read BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notification_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_notification_user ON notifications(user_id);
CREATE INDEX idx_notification_read ON notifications(is_read);



-- =========================
-- TRIP LIVE STATUS (OPTIONAL CACHE)
-- =========================

CREATE TABLE trip_live_status (

    trip_id INTEGER PRIMARY KEY,

    current_stop_id INTEGER,

    delay_minutes INTEGER DEFAULT 0,

    last_lat DOUBLE PRECISION,
    last_lon DOUBLE PRECISION,

    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_live_trip
        FOREIGN KEY(trip_id)
        REFERENCES schedule_trips(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_live_stop
        FOREIGN KEY(current_stop_id)
        REFERENCES stops(id)
        ON DELETE SET NULL
);

CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    template_type TEXT DEFAULT 'auto',

    bus_count INTEGER NOT NULL,
    driver_count INTEGER NOT NULL,

    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_template_user
        FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL
);

CREATE TABLE template_records (
    id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL,
    route_id TEXT NOT NULL,
    start_time TIME NOT NULL,
    -- busNo INTEGER NOT NULL,
    -- driverNo INTEGER NOT NULL,

    CONSTRAINT fk_template_record_template
        FOREIGN KEY (template_id)
        REFERENCES templates(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_template_record_route
        FOREIGN KEY (route_id)
        REFERENCES routes(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_template_records_template
ON template_records(template_id);

CREATE TABLE ob_data (
    id SERIAL PRIMARY KEY,

    route_id TEXT NOT NULL,
    stop_id INTEGER NOT NULL,

    boarding_count INTEGER DEFAULT 0,
    offboarding_count INTEGER DEFAULT 0,

    trip_datetime TIMESTAMP NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ob_route
        FOREIGN KEY(route_id)
        REFERENCES routes(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_ob_stop
        FOREIGN KEY(stop_id)
        REFERENCES stops(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_ob_route_time ON ob_data(route_id, trip_datetime);
CREATE INDEX idx_ob_stop ON ob_data(stop_id);


COMMIT;