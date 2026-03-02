-- Safe cleanup if re-running
DROP TABLE IF EXISTS observation_data;
DROP TABLE IF EXISTS admin_overrides;
DROP TABLE IF EXISTS stop_times;
DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS service;
DROP TABLE IF EXISTS crew_data;
DROP TABLE IF EXISTS bus_data;
DROP TABLE IF EXISTS routes;
DROP TABLE IF EXISTS stops;
DROP TABLE IF EXISTS users;

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    role VARCHAR(50),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

-- Stops table
CREATE TABLE stops (
    stop_id SERIAL PRIMARY KEY,
    stop_code VARCHAR(20),
    stop_name VARCHAR(150) NOT NULL,
    stop_lat NUMERIC,
    stop_lon NUMERIC
);

-- Routes table
CREATE TABLE routes (
    route_id SERIAL PRIMARY KEY,
    route_short_name VARCHAR(50),
    route_long_name VARCHAR(150),
    stops INT[],
    route_code VARCHAR(50),
    stop_time INT[],
    stop_dist INT[]
);

-- Bus table
CREATE TABLE bus_data (
    bus_id SERIAL PRIMARY KEY,
    bus_no VARCHAR(50) NOT NULL,
    seating_capacity INT NOT NULL,
    max_capacity INT NOT NULL
);

-- Crew table
CREATE TABLE crew_data (
    crew_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    post VARCHAR(50),
    experience INT
);

-- Service table
CREATE TABLE service (
    service_id SERIAL PRIMARY KEY,
    driver_id INT REFERENCES users(user_id),
    conductor_id INT REFERENCES users(user_id),
    notes TEXT
);

-- Trips table
CREATE TABLE trips (
    trip_id SERIAL PRIMARY KEY,
    route_id INT REFERENCES routes(route_id),
    service_id INT REFERENCES service(service_id),
    date DATE NOT NULL
);

-- Stop times table
CREATE TABLE stop_times (
    id SERIAL PRIMARY KEY,
    trip_id INT REFERENCES trips(trip_id),
    stop_id INT REFERENCES stops(stop_id),
    arrival_time TIME,
    departure_time TIME,
    boarding_in INT,
    boarding_out INT
);

-- Admin overrides table
CREATE TABLE admin_overrides (
    id SERIAL PRIMARY KEY,
    trip_id INT REFERENCES trips(trip_id),
    delta_minutes INT,
    effective_date DATE,
    reason TEXT
);

-- Observation data table
CREATE TABLE observation_data (
    id SERIAL PRIMARY KEY,
    bus_no VARCHAR(50),
    route_id INT REFERENCES routes(route_id),
    stop_id INT REFERENCES stops(stop_id),
    boarding_count INT,
    alighting_count INT,
    timestamp TIMESTAMP DEFAULT NOW()
);