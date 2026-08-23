# SmartBus Scheduler

> Automated Bus Scheduling and Route Management System

SmartBus Scheduler is a public transportation management platform designed to automate bus timetable generation, driver assignment, route management, and real-time bus monitoring. The system combines scheduling optimization, GIS/map services, GPS updates, and role-based interfaces for administrators, drivers, and passengers.

## Overview

Traditional bus operations often depend on manual timetable creation and route planning, which can lead to scheduling conflicts, inefficient fleet utilization, delays, and limited visibility for passengers. SmartBus Scheduler centralizes these operations in a single platform.

The system processes transport and operational data such as:

* Bus availability and capacity
* Driver availability and shift constraints
* Routes and stop sequences
* Timetable and trip data
* Passenger demand
* Traffic conditions and road distances
* GPS and real-time vehicle location data

This information is used to generate practical, conflict-free schedules and provide route and tracking information to different users.

## Key Features

### Automated Scheduling

* Generate bus schedules from fleet, route, timetable, and driver data
* Consider operational constraints such as driver working hours, route distance, time intervals, and bus availability
* Reduce overlapping trips and scheduling conflicts
* Balance driver workload and fleet utilization
* Support optimization using Genetic Algorithm / NSGA-based approaches

### Route Management

* Create, update, and manage routes
* Manage bus stops and route structures
* Calculate route distances and estimated travel times
* Integrate map/GIS services for route visualization
* Support traffic-aware routing and future dynamic route adjustments

### Fleet and Driver Management

* Maintain bus and driver records
* Assign drivers to generated schedules
* Track driver availability and workload
* Provide route and trip information to drivers

### Dataset Upload and Processing

Administrators can import structured transport datasets, including:

* Stops data
* Routes data
* Route timeplans
* Bus fleet data
* Driver data
* Observation or operational data

Uploaded data is validated and preprocessed before being used by the scheduling and optimization workflow.

### Real-Time Tracking

* Receive live GPS updates from drivers or vehicles
* Display current bus locations
* Provide estimated arrival times
* Surface delays and route deviations
* Keep dashboards updated through real-time communication

### Notifications and Alerts

* Driver assignment notifications
* Schedule change alerts
* Trip cancellation updates
* Shift reminders
* Route-change and delay notifications

### Passenger Experience

Passengers can:

* Search buses and routes
* View schedules and timings
* Track live bus locations
* View estimated arrival times
* Receive delay and route updates

## User Roles

| Role                     | Capabilities                                                                             |
| ------------------------ | ---------------------------------------------------------------------------------------- |
| **Admin**                | Manage datasets, buses, drivers, stops, routes, schedules, and system operations         |
| **Driver**               | View assigned trips and routes, receive notifications, and provide live location updates |
| **Passenger / Customer** | Search routes, view schedules, track buses, and check ETAs and delays                    |

## System Architecture

The platform follows a modular architecture:

```text
                 ┌──────────────────────────────┐
                 │        Input Data Layer      │
                 │ GTFS / Routes / Stops        │
                 │ Fleet / Drivers / Demand     │
                 │ Traffic / GPS / Observations │
                 └──────────────┬───────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │ Data Processing &            │
                 │ Optimization Engine          │
                 │                              │
                 │ • Constraint validation      │
                 │ • Schedule optimization      │
                 │ • Driver assignment          │
                 │ • Conflict validation        │
                 └──────────────┬───────────────┘
                                │
                ┌───────────────┼────────────────┐
                ▼               ▼                ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ Admin Module │ │ Driver Module│ │ Passenger   │
        │              │ │              │ │ Module      │
        └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
               │                │                │
               └────────────────┼────────────────┘
                                ▼
                 ┌──────────────────────────────┐
                 │ Visual Management Platform   │
                 │ Maps • Tracking • Alerts     │
                 │ Reporting • Analytics        │
                 └──────────────────────────────┘
```

## Technology Stack

| Area              | Technologies / Services                                                    |
| ----------------- | -------------------------------------------------------------------------- |
| Web frontend      | React.js                                                                   |
| Mobile frontend   | Flutter                                                                    |
| Backend           | Python with FastAPI or Flask                                               |
| Database          | MySQL or PostgreSQL                                                        |
| Scheduling        | Genetic Algorithm / NSGA-based optimization                                |
| Maps & routing    | Google Maps API and GIS services                                           |
| Real-time updates | WebSockets                                                                 |
| Notifications     | Firebase Cloud Messaging or equivalent notification APIs                   |
| Tracking          | GPS services                                                               |
| APIs              | REST APIs                                                                  |
| Data              | GTFS-style transport data and CSV datasets                                 |
| Testing           | Functional, API, database, performance, usability, and concurrency testing |

> **Note:** The project report presents some technologies as alternatives. Check the repository source code and configuration files to determine the exact implementation used in this codebase.

## Data Flow

1. Transport and operational data is collected from GTFS datasets, fleet records, driver information, demand data, GPS feeds, and traffic observations.
2. Data is validated and preprocessed.
3. Operational constraints are applied.
4. The scheduling engine generates candidate schedules.
5. Optimization evaluates schedules for efficiency, waiting time, and resource utilization.
6. Generated schedules are validated for conflicts and operational feasibility.
7. Approved schedules are made available to administrators and drivers.
8. GPS and operational updates continuously feed the tracking and dashboard modules.
9. Passengers receive schedule, location, ETA, and delay information.

## Expected Input Data

Depending on the implementation, the system may use CSV or GTFS-style datasets such as:

```text
stops_data.csv
routes_data.csv
routes_timeplan.csv
buses_data.csv
drivers_data.csv
observation_data_*.csv
```

The exact filenames and schemas should match the repository's import or dataset-upload implementation.

## Getting Started

Because this README was generated from the project report rather than the repository source tree, the exact commands, package names, environment variables, and startup scripts cannot be confirmed from the report alone.

A typical setup for the described architecture would be:

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Configure environment variables

Create the appropriate environment file used by the implementation and configure values such as:

```env
DATABASE_URL=<database-connection-string>
GOOGLE_MAPS_API_KEY=<maps-api-key>
FIREBASE_CONFIG=<firebase-configuration>
```

The actual variable names must be taken from the repository's configuration files.

### 3. Set up the backend

For a Python backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then start the application using the repository's configured entry point.

### 4. Set up the web frontend

If the repository contains a React frontend:

```bash
npm install
npm run dev
```

or use the package scripts defined in `package.json`.

### 5. Set up the mobile application

If the Flutter application is included:

```bash
flutter pub get
flutter run
```

### 6. Configure the database

Create the database, configure the connection string, and run the project's migrations, schema scripts, or initialization process.

### 7. Load transport data

Upload or import the required stops, routes, timetable, bus, driver, and observation datasets through the admin interface or the repository's import utilities.

## Testing

The project report describes testing across the following areas:

* Dashboard functionality
* Navigation between system modules
* Real-time GPS updates
* Multi-route schedule generation
* GTFS/dataset import
* ETA calculations
* Route optimization
* Performance under larger scheduling workloads
* Dashboard responsiveness under high GPS update volume
* Invalid input handling
* Concurrent GPS processing
* Parallel schedule generation
* Background task synchronization

## Future Enhancements

Potential future work identified in the project includes:

* Dynamic route optimization using live traffic and road conditions
* AI-based passenger demand prediction
* Improved bus frequency recommendations for peak and non-peak periods
* Additional GPS and IoT integrations
* Mobile application expansion
* Smart ticketing integration
* Predictive analytics and advanced operational reporting

## Project Team

* Ashna Brito
* Narendra Dukhande
* Lenoy Geo Thomas
* Sanchita Warade

**Supervisor:** Prof. Prasad Padalkar

**Institution:** Department of Information Technology, Don Bosco Institute of Technology, University of Mumbai

## Disclaimer

This README is based on the supplied project report. It documents the project's stated objectives, architecture, modules, technology choices, and implementation plan. Repository-specific details such as exact directory structure, API endpoints, package versions, environment variable names, database schema, and startup commands should be verified against the actual source code before publishing this README as final documentation.
