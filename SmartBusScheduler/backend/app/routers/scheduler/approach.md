
---

# MAIN FLOW

```python
main(start_date, end_date):

  templates = generate_templates()

  schedule = generate_schedule(date1, date2, templates)

  return schedule
```

---

# TEMPLATE GENERATION

```python
generate_templates():

  categories = ["weekday", "saturday", "sunday"]

  templates = {}

  for category in categories:

      demand = compute_demand(category)

      trips = generate_trips(demand)

      template = assign_abstract_resources(trips)

      template = assign_driver_shifts(template)

      templates[category] = template

      store_template(category, template)

  return templates
```

---

# 1. DEMAND COMPUTATION

```python
compute_demand(category):

  raw_data = DB.get_OB_data(category)

  demand = {}   # demand[route][slot] = value

  # initialize
  for record in raw_data:

      route = record.route_id
      slot = floor_to_slot(record.timestamp)

      if route not in demand:
          demand[route] = {}

      if slot not in demand[route]:
          demand[route][slot] = []

      demand[route][slot].append(record.passenger_count)

  # average demand
  for route in demand:
      for slot in demand[route]:
          demand[route][slot] = average(demand[route][slot])

  # sort slots
  ordered_slots = sort_slots(demand)

  # future 30-min smoothing
  future_demand = {}

  for route in demand:

      future_demand[route] = {}

      for i in range(len(ordered_slots)):

          slot = ordered_slots[i]

          total = 0

          for j in range(i, min(i+3, len(ordered_slots))):
              next_slot = ordered_slots[j]
              total += demand[route].get(next_slot, 0)

          future_demand[route][slot] = total

  return future_demand
```

---

# 2. TRIP GENERATION

```python
generate_trips(demand):

  trips = []

  for route in demand:

      route_time = DB.get_route_travel_time(route)

      for slot in demand[route]:

          passengers = demand[route][slot]

          required_trips = ceil(passengers / BUS_CAPACITY)

          if required_trips == 0:
              continue

          slot_start, slot_end = get_slot_window(slot)

          spacing = (slot_end - slot_start) / required_trips

          for i in range(required_trips):

              start_time = slot_start + i * spacing
              end_time = start_time + route_time

              trip = {
                  "route": route,
                  "start_time": start_time,
                  "end_time": end_time,
                  "bus": None,
                  "driver": None
              }

              trips.append(trip)

  trips = sort(trips, key=start_time)

  return trips
```

---

# 3. ABSTRACT RESOURCE ASSIGNMENT

```python
assign_abstract_resources(trips):

  bus_pool = []
  driver_pool = []

  bus_free_time = {}
  driver_free_time = {}

  bus_last_trip = {}
  driver_last_trip = {}

  bus_id_counter = 1
  driver_id_counter = 1

  for trip in trips:

      # ---------- BUS ASSIGNMENT ----------
      assigned_bus = None

      for bus in bus_pool:

          if bus_free_time[bus] <= trip.start_time:

              rest = get_rest_time(bus_last_trip[bus], trip)

              if bus_free_time[bus] + rest <= trip.start_time:
                  assigned_bus = bus
                  break

      if assigned_bus is None:
          assigned_bus = "B" + str(bus_id_counter)
          bus_id_counter += 1

          bus_pool.append(assigned_bus)
          bus_free_time[assigned_bus] = 0
          bus_last_trip[assigned_bus] = None

      # ---------- DRIVER ASSIGNMENT ----------
      assigned_driver = None

      for driver in driver_pool:

          if driver_free_time[driver] <= trip.start_time:

              rest = get_rest_time(driver_last_trip[driver], trip)

              if driver_free_time[driver] + rest <= trip.start_time:
                  assigned_driver = driver
                  break

      if assigned_driver is None:
          assigned_driver = "D" + str(driver_id_counter)
          driver_id_counter += 1

          driver_pool.append(assigned_driver)
          driver_free_time[assigned_driver] = 0
          driver_last_trip[assigned_driver] = None

      # ---------- ASSIGN ----------
      trip["bus"] = assigned_bus
      trip["driver"] = assigned_driver

      # ---------- UPDATE STATE ----------
      rest_bus = get_rest_time(bus_last_trip[assigned_bus], trip)
      rest_driver = get_rest_time(driver_last_trip[assigned_driver], trip)

      bus_free_time[assigned_bus] = trip.end_time + rest_bus
      driver_free_time[assigned_driver] = trip.end_time + rest_driver

      bus_last_trip[assigned_bus] = trip
      driver_last_trip[assigned_driver] = trip

  template = {
      "trips": trips,
      "bus_pool": bus_pool,
      "driver_pool": driver_pool,
      "bus_count": len(bus_pool),
      "driver_count": len(driver_pool)
  }

  return template
```

---

# REST TIME LOGIC

```python
get_rest_time(prev_trip, current_trip):

  if prev_trip is None:
      return 0

  if prev_trip["route"] == current_trip["route"]:
      return 10   # minutes
  else:
      return 20
```

---

# 4. DRIVER SHIFT ASSIGNMENT

```python
assign_driver_shifts(template):

  drivers = template["driver_pool"]
  trips = template["trips"]

  shifts = {
      "morning": (5:00, 13:00),
      "afternoon": (13:00, 21:00),
      "night": (21:00, 5:00)
  }

  shift_map = {}

  # divide drivers
  per_shift = ceil(len(drivers) / len(shifts))

  index = 0
  for shift in shifts:
      shift_map[shift] = drivers[index:index+per_shift]
      index += per_shift

  driver_shift_usage = {d: 0 for d in drivers}

  for trip in trips:

      shift = get_shift_from_time(trip["start_time"])

      if trip["driver"] not in shift_map[shift]:

          # allow controlled double shift
          driver_shift_usage[trip["driver"]] += 1

          if driver_shift_usage[trip["driver"]] > MAX_DOUBLE_SHIFT:
              # swap driver (optional improvement)
              continue

  template["shift_map"] = shift_map

  return template
```

---

# SCHEDULE GENERATION

```python
generate_schedule(start_date, end_date, templates):
    schedules=[]
    for date in range(start_date, end_date+1):

        category = get_category(date)

        template = templates[category]

        resources = fetch_real_resources()

        ranked = rank_resources(resources)

        mapping = map_abstract_to_real(template, ranked)

        schedule = assign_with_constraints(template, mapping)

        schedules.add(schedule)

  return schedules
```

---

# RESOURCE RANKING

```python
rank_resources(resources):

  drivers = resources["drivers"]
  buses = resources["buses"]

  drivers = sort(drivers, key=driver_usage_last_3_days)

  buses = sort(buses, key=bus_last_used_time)

  return {
      "drivers": drivers,
      "buses": buses
  }
```

---

# MAPPING

```python
map_abstract_to_real(template, ranked):

  mapping = {}

  for i in range(len(template["bus_pool"])):
      mapping[template["bus_pool"][i]] = ranked["buses"][i]

  for i in range(len(template["driver_pool"])):
      mapping[template["driver_pool"][i]] = ranked["drivers"][i]

  return mapping
```

---

# FINAL ASSIGNMENT WITH SAFETY

```python
assign_with_constraints(template, mapping):

  real_busy_time = {}

  schedule = []

  for trip in template["trips"]:

      real_bus = mapping[trip["bus"]]
      real_driver = mapping[trip["driver"]]

      if not is_available(real_bus, trip, real_busy_time):
          real_bus = find_alternate_bus(real_busy_time, trip)

      if not is_available(real_driver, trip, real_busy_time):
          real_driver = find_alternate_driver(real_busy_time, trip)

      # assign
      trip["bus"] = real_bus
      trip["driver"] = real_driver

      update_busy(real_busy_time, real_bus, trip)
      update_busy(real_busy_time, real_driver, trip)

      schedule.append(trip)

  return schedule
```

---

# AVAILABILITY CHECK

```python
is_available(resource, trip, real_busy_time):

  if resource not in real_busy_time:
      return True

  return real_busy_time[resource] <= trip["start_time"]
```

---

# UPDATE BUSY STATE

```python
update_busy(real_busy_time, resource, trip):

  rest = get_rest_time(None, trip)  # or track previous real trip

  real_busy_time[resource] = trip["end_time"] + rest
```
