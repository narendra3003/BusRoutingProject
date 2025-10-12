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


CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    role VARCHAR(20) CHECK (role IN ('customer', 'admin', 'driver')),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- 10 users (1 admin, 4 drivers, 3 uploaders, 2 customers)
INSERT INTO users (role, name, email, password_hash) VALUES
('admin', 'Asha Mehra', 'asha.mehra@delhitransit.local', 'pbkdf2_hash_admin_01'),
('driver', 'Ramesh Kumar', 'ramesh.kumar@delhitransit.local', 'pbkdf2_hash_driver_02'),
('driver', 'Suresh Yadav', 'suresh.yadav@delhitransit.local', 'pbkdf2_hash_driver_03'),
('driver', 'Aman Singh', 'aman.singh@delhitransit.local', 'pbkdf2_hash_driver_04'),
('driver', 'Vikram Patel', 'vikram.patel@delhitransit.local', 'pbkdf2_hash_driver_05'),
('customer', 'Priya Sharma', 'priya.sharma@delhitransit.local', 'pbkdf2_hash_uploader_06'),
('customer', 'Neha Gupta', 'neha.gupta@delhitransit.local', 'pbkdf2_hash_uploader_07'),
('customer', 'Rohit Verma', 'rohit.verma@delhitransit.local', 'pbkdf2_hash_uploader_08'),
('customer', 'Sana Khan', 'sana.khan@example.com', 'pbkdf2_hash_customer_09'),
('customer', 'Aditya Rao', 'aditya.rao@example.com', 'pbkdf2_hash_customer_10');

CREATE TABLE stops (
    stop_id SERIAL PRIMARY KEY,
    stop_code VARCHAR(20) UNIQUE,
    stop_name VARCHAR(150) NOT NULL,
    stop_lat DECIMAL(9,6),
    stop_lon DECIMAL(9,6)
);

-- 80 stops (Delhi & nearby localities themed)
INSERT INTO stops (stop_code, stop_name, stop_lat, stop_lon) VALUES
('DL001','Connaught Place - Inner Circle',28.632042,77.219185),
('DL002','Janpath Crossing',28.632800,77.218200),
('DL003','Rajiv Chowk Metro Station',28.631519,77.216726),
('DL004','Palika Bazaar',28.631000,77.216000),
('DL005','Kashmiri Gate Interchange',28.661900,77.239000),
('DL006','Old Delhi Railway Station',28.656159,77.230328),
('DL007','Chandni Chowk',28.656159,77.230328),
('DL008','Red Fort / Lal Qila',28.656159,77.241020),
('DL009','Jama Masjid',28.650700,77.233400),
('DL010','Daryaganj',28.644200,77.233100),
('DL011','Khan Market',28.598500,77.219400),
('DL012','Nehru Place',28.549944,77.269450),
('DL013','Lajpat Nagar',28.576130,77.249300),
('DL014','Nizamuddin',28.586932,77.249920),
('DL015','AIIMS',28.567190,77.210040),
('DL016','South Ex. (South Extension)',28.590087,77.212527),
('DL017','Green Park',28.568974,77.199502),
('DL018','Hauz Khas',28.549722,77.200833),
('DL019','Kalkaji Mandir',28.553812,77.256095),
('DL020','Lajpat Bhawan',28.576900,77.248100),
('DL021','Rajouri Garden',28.642530,77.105660),
('DL022','Kirti Nagar',28.649400,77.131300),
('DL023','Punjabi Bagh',28.677400,77.143200),
('DL024','Pitampura',28.712600,77.139100),
('DL025','Rohini Sector 18',28.756000,77.110000),
('DL026','Azadpur Mandi',28.703829,77.167763),
('DL027','Model Town',28.700100,77.189000),
('DL028','GTB Nagar',28.675736,77.216995),
('DL029','Shahdara',28.669500,77.279000),
('DL030','Dilshad Garden',28.694100,77.304100),
('DL031','Mayur Vihar Phase 1',28.618400,77.297200),
('DL032','Yamuna Vihar',28.693900,77.234500),
('DL033','Anand Vihar ISBT',28.650000,77.318000),
('DL034','Indraprastha',28.616020,77.243200),
('DL035','ITO Crossing',28.6320,77.2385),
('DL036','Kashmere Gate Bus Stand',28.661900,77.239000),
('DL037','Seelampur',28.668800,77.262600),
('DL038','Welcome',28.682200,77.256300),
('DL039','New Delhi Railway Station',28.646700,77.2229),
('DL040','Pahar Ganj',28.645900,77.205800),
('DL041','Karol Bagh',28.651700,77.1950),
('DL042','Rajinder Nagar',28.6540,77.1978),
('DL043','Moti Bagh',28.5825,77.1656),
('DL044','Patel Nagar',28.6501,77.1652),
('DL045','Shastri Nagar',28.6922,77.1288),
('DL046','Vikas Puri',28.6530,77.1014),
('DL047','Khyala',28.6520,77.1216),
('DL048','Qutub Minar',28.524428,77.185455),
('DL049','Saket',28.517100,77.210000),
('DL050','Mehrauli',28.5240,77.1860),
('DL051','Chattarpur',28.5238,77.1837),
('DL052','Huda City Centre (ish)',28.4595,77.0266),
('DL053','Dwarka Sector 21',28.5734,77.0200),
('DL054','Janakpuri West',28.6414,77.0880),
('DL055','Uttam Nagar',28.6117,77.0648),
('DL056','Tilak Nagar',28.6420,77.0793),
('DL057','Sultanpur',28.4936,77.1100),
('DL058','Gurgaon Sector 14 (nearby)',28.4689,77.0466),
('DL059','Noida Sector 18 (nearby)',28.5720,77.3570),
('DL060','Rajpath',28.6140,77.1990),
('DL061','India Gate',28.6129,77.2295),
('DL062','Minto Road',28.6336,77.2116),
('DL063','Pragati Maidan',28.6275,77.2389),
('DL064','Bhikaji Cama Place',28.5597,77.1809),
('DL065','Janakpuri East',28.6507,77.0952),
('DL066','Moti Nagar Depot',28.6463,77.1527),
('DL067','Ashok Vihar',28.6818,77.1831),
('DL068','Rithala',28.7200,77.1170),
('DL069','Kanjhawala',28.7500,77.0200),
('DL070','Narela',28.8589,77.0980),
('DL071','Alipur',28.7350,77.1600),
('DL072','Bawana',28.7730,77.0750),
('DL073','Mangolpuri',28.7140,77.1240),
('DL074','Shalimar Bagh',28.6930,77.1440),
('DL075','Wazirpur',28.6760,77.1470),
('DL076','Ghaziabad Crossing',28.6692,77.4538),
('DL077','Loni (Near Ghaziabad)',28.7444,77.2916),
('DL078','Badarpur Border',28.5333,77.3011),
('DL079','Tughlakabad',28.5413,77.2700),
('DL080','Mehrauli Archaeological Park',28.5175,77.1850);

CREATE TABLE routes (
    route_id SERIAL PRIMARY KEY,
    route_short_name VARCHAR(20),
    route_long_name VARCHAR(150),
    stops INTEGER[]  -- array of stop_id values
);

-- For readability I choose sets of stops (IDs 1..80). 
-- Each route references a list of stop ids (16-20 ids each).
INSERT INTO routes (route_short_name, route_long_name, stops) VALUES
('D1','Central Circle - Connaught Place ↔ Old Delhi', ARRAY[1,2,3,4,39,7,6,10,35,34,33,32,31,30,29,28]),
('D2','South-East Link - AIIMS ↔ Kalkaji ↔ Nehru Place', ARRAY[15,16,17,18,19,12,14,13,20,49,48,50,51,34,35,60]),
('D3','West-Delhi Connector - Rajouri Garden ↔ Janakpuri ↔ Uttam Nagar', ARRAY[21,22,44,66,41,40,54,55,56,21,22,23,24,46,65,66]),
('D4','North-South Express - Kashmiri Gate ↔ Connaught Place ↔ India Gate', ARRAY[5,36,3,1,60,61,35,34,63,62,10,11,17,18,19,20]),
('D5','Ring Road Shuttle - Karol Bagh ↔ Rajendra Nagar ↔ Patel Nagar', ARRAY[41,42,44,66,43,64,12,13,14,15,16,17,18,19,20]),
('D6','Outer Ring - Pitampura ↔ Rohini ↔ Rithala', ARRAY[24,25,68,67,69,70,71,72,73,74,75,23,22,21,46,44]),
('D7','Airport Link (partial) - Pahar Ganj ↔ Dhaula Kuan ↔ Mehrauli', ARRAY[40,39,35,60,61,63,64,48,50,51,80,49,34,33,32,31]),
('D8','East Corridor - Anand Vihar ↔ Indraprastha ↔ Mayur Vihar', ARRAY[33,34,35,31,32,30,29,28,27,26,59,58,57,78,79,80]),
('D9','Gurgaon/Noida Connector - Huda/GGN ↔ Noida ↔ Saket', ARRAY[52,58,59,49,50,51,31,34,35,15,49,53,54,55,56,49]),
('D10','South-West Loop - Qutub Minar ↔ Chhattarpur ↔ Saket', ARRAY[48,50,51,49,15,16,17,18,51,48,80,50,49,35,34,33]);


CREATE TABLE service (
    service_id SERIAL PRIMARY KEY,
    driver_id INT REFERENCES users(user_id),
    conductor_id INT REFERENCES users(user_id),
    notes TEXT
);

-- Small set of service assignments (driver_id references users inserted earlier).
-- We have users with user_id = 1..10 in insertion order; drivers are user_id 2..5 from above.
INSERT INTO service (driver_id, conductor_id, notes) VALUES
(2, NULL, 'Morning shift - Central Corridor'),
(3, NULL, 'Afternoon shift - West line'),
(4, NULL, 'Night shift - Ring Road');


CREATE TABLE trips (
    trip_id SERIAL PRIMARY KEY,
    route_id INT REFERENCES routes(route_id),
    service_id INT REFERENCES service(service_id),
    date DATE NOT NULL
);

-- Representative trips (5 rows). If you want many trips per route, see my notes at the end.
INSERT INTO trips (route_id, service_id, date) VALUES
(1, 1, '2025-10-10'),
(2, 2, '2025-10-10'),
(3, 2, '2025-10-11'),
(4, 3, '2025-10-11'),
(5, 1, '2025-10-12');



CREATE TABLE stop_times (
    id SERIAL PRIMARY KEY,
    trip_id INT REFERENCES trips(trip_id),
    stop_id INT REFERENCES stops(stop_id),
    arrival_time TIME,
    departure_time TIME,
    boarding_in INT,
    boarding_out INT
);

-- Representative stop times (only a few rows per trip so total inserts remain controlled)
INSERT INTO stop_times (trip_id, stop_id, arrival_time, departure_time, boarding_in, boarding_out) VALUES
(1, 1, '08:00:00', '08:02:00', 12, 0),
(1, 3, '08:10:00', '08:12:00', 5, 2),
(2, 15, '09:15:00', '09:16:00', 20, 0),
(3, 21, '10:00:00', '10:03:00', 8, 1),
(4, 5, '18:30:00', '18:32:00', 3, 0),
(5, 48, '07:40:00', '07:41:00', 6, 0);


CREATE TABLE admin_overrides (
    id SERIAL PRIMARY KEY,
    trip_id INT REFERENCES trips(trip_id),
    delta_minutes INT,
    effective_date DATE,
    reason TEXT
);

INSERT INTO admin_overrides (trip_id, delta_minutes, effective_date, reason) VALUES
(1, 10, '2025-10-10', 'Road construction near Connaught Place caused delay'),
(4, -5, '2025-10-11', 'Adjusted early departure to avoid evening congestion');


CREATE TABLE observation_data (
    id SERIAL PRIMARY KEY,
    bus_no VARCHAR(30),
    route_id INT REFERENCES routes(route_id),
    stop_id INT REFERENCES stops(stop_id),
    boarding_count INT,
    alighting_count INT,
    timestamp TIMESTAMP DEFAULT NOW()
);

INSERT INTO observation_data (bus_no, route_id, stop_id, boarding_count, alighting_count, timestamp) VALUES
('DL-BUS-1001', 1, 1, 12, 0, '2025-10-10 08:02:00'),
('DL-BUS-1002', 2, 15, 20, 0, '2025-10-10 09:16:00');


CREATE TABLE bus_data (
    bus_id SERIAL PRIMARY KEY,
    passenger_cap_count INT NOT NULL
);

INSERT INTO bus_data (passenger_cap_count) VALUES
(60);


CREATE TABLE crew_data (
    crew_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    post VARCHAR(20) CHECK (post IN ('Driver', 'Conductor')),
    experience INT CHECK (experience >= 0)
);

INSERT INTO crew_data (name, post, experience) VALUES
('Ramesh Kumar', 'Driver', 12);


-- select * from users;
-- select * from stops;
-- select * from routes;
-- select * from admin_overrides;
-- select * from trips;
-- select * from stop_times;
-- select * from observation_data;
-- select * from crew_data;
-- select * from bus_data;
-- select * from services;