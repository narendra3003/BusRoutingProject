🧾 Bus Operations Analysis — Function Reference & Interpretation Guide

This document describes every function in the 6 bus analysis modules, what it measures, how it’s computed, and how to interpret the results.

🚏 1️⃣ Passenger Flow & Density Analysis

File: _1_passenger_flow.py
Purpose: Understand how passengers are distributed over time, stops, and routes.

🔹 passenger_flow_over_time(df)

What it shows:
Line plot of total passengers boarding per hour of the day.

Calculation:

df.groupby("hour")["boarding_in"].sum()


Interpretation:

High peaks between 7–10 AM and 17–22 PM → strong commuter behavior.

Flat distribution → balanced, non-office-hour demand.

A “dip” between 12–15 → off-peak (good sign of expected midday lull).

If values are unusually low:
May indicate low service frequency or data generation bias for that date.

🔹 passenger_density_per_stop(df)

What it shows:
Net passenger flow per stop (total boarding minus alighting).

Formula:

net_flow = Σ(boarding_in) – Σ(boarding_out)


Interpretation:

Positive → boarding-heavy stop (e.g., residential area).

Negative → alighting-heavy stop (e.g., offices or city center).

Near-zero → balanced stop (intermediate or transfer stop).

Diagnostic Value:
Helps decide which stops need more shelters or priority boarding systems.

🔹 passenger_heatmap(df)

What it shows:
Heatmap of passenger flow by route (rows) vs hour (columns).

Interpretation:

Bright areas = routes with high load at specific hours.

Consistent brightness = stable ridership.

Sharp spikes = high temporal variation (good for dynamic scheduling).

🚌 2️⃣ Bus Usage & Load Factor Analysis

File: _2_bus_usage.py
Purpose: Evaluate bus-level utilization, load distribution, and overcrowding.

🔹 avg_occupancy_by_route(df)

What it shows:
Average number of passengers per route (boarding minus alighting totals).

Formula:

net_passengers = Σ(boarding_in) – Σ(boarding_out)


Interpretation:

High values → long, busy routes or higher ridership.

Negative values (rare) → possible data artifact; means more passengers alighted than boarded (should only happen at terminal stops).

🔹 bus_utilization(df)

What it shows:
Total passengers handled by each bus across the day.

Formula:

total_passengers = Σ(boarding_in + boarding_out)


Interpretation:

High = high usage (may need maintenance more often).

Low = underutilized bus (possible resource redistribution).

🔹 overcrowding_index(df, buses_df)

What it shows:
Percent of trips where total passengers exceed bus capacity.

Formula:

overcrowded = Σ(boarding_in - boarding_out) > max_capacity


Interpretation:

20% = frequent overcrowding → add more trips or larger buses.

<5% = healthy utilization.

Negative load values → means bus had more people getting off (normal after terminals).

⏰ 3️⃣ Delay & Punctuality Analysis

File: _3_delay_analysis.py
Purpose: Understand service reliability and its link to demand.

🔹 avg_delay_per_route(df)

What it shows:
Average delay in minutes per route.

Formula:

mean(delay_mins) per route


Interpretation:

0–3 min = excellent.

4–8 min = moderate traffic or crowding.

8 min = route inefficiency or bottlenecks.

If negative:
Means the bus arrived early — unrealistic in real life, but could appear in synthetic data (early arrival simulation).

🔹 delay_vs_hour(df)

What it shows:
How average delay changes across the day.

Interpretation:

Morning or evening spikes → congestion or high demand.

Flat line → consistent service.

Use Case:
Helps identify if schedule should be adjusted for peak hours.

🔹 delay_vs_load(df)

What it shows:
Scatter plot comparing passenger load vs delay.

Interpretation:

Upward trend = more passengers → higher delay (crowding effect).

Random scatter = no clear correlation → delays likely due to traffic, not load.

Negative load:
Indicates more alighting than boarding at that moment — typical for return trips.

⏱ 4️⃣ Passenger Waiting Time Estimation

File: _4_waiting_time.py
Purpose: Estimate how long passengers wait for buses and when waiting peaks occur.

🔹 estimate_waiting_time(df)

What it shows:
Average waiting time per route (based on spacing between trips).

Formula (simplified):

avg_wait_time = mean(interval between consecutive arrivals)


Interpretation:

<10 min = good service.

10–20 min = moderate.

20 min = poor service or low frequency.

Negative or NaN:
Means insufficient data points for that route (only one trip logged).

🔹 waiting_time_by_hour(df)

What it shows:
Estimated waiting time trend across hours of the day.

Formula:

wait_time ≈ base_wait + avg_delay


(default base_wait = 5 min)

Interpretation:

Peaks outside morning/evening = uneven headways or delays.

Very low values → frequent buses (good).

🌇 5️⃣ Peak Hour Pattern Comparison

File: _5_peak_pattern.py
Purpose: Compare morning and evening directional demand patterns.

🔹 morning_vs_evening_boardings(df)

What it shows:
Total boardings per route in morning (7–10) vs evening (17–22).

Formula:

Σ(boarding_in) grouped by hour range


Interpretation:

Morning-high routes = commuters going into city.

Evening-high = commuters returning.

Equal → balanced intra-city routes.

Diagnostic:
Useful for balancing trip counts between up/down directions.

🔹 route_direction_flow(df)

What it shows:
Total hourly passenger count for _up vs _down routes.

Interpretation:

“Up” routes high in morning and “down” high in evening → classic commuter corridor.

Flat = circular/short feeder service.

If both directions high all day:
Indicates bidirectional demand — good for all-day frequency.

⚙️ 6️⃣ Service Efficiency Metrics

File: _6_service_efficiency.py
Purpose: Provide performance KPIs for service quality, capacity use, and reliability.

🔹 on_time_performance(df)

What it shows:
% of records where delay_mins <= 3.

Formula:

on_time_rate = (delay_mins <= 3) / total * 100


Interpretation:

85% = very reliable.

70–85% = acceptable.

<70% = scheduling or congestion issues.

🔹 load_factor(df, buses_df)

What it shows:
Average passenger load as % of total capacity.

Formula:

load_factor = mean(net_load) / mean(max_capacity)


Interpretation:

<60% = underutilized fleet.

60–90% = efficient.

100% = overcrowded conditions.

If negative:
Implies more people alighting — should only appear at endpoints or start of routes.

🔹 overcrowding_index(df, buses_df)

What it shows:
Percentage of trips exceeding their bus’s max capacity.

Formula:

(overcrowded_trips / total_trips) * 100


Interpretation:

<5% = healthy.

20% = chronic overcrowding → increase capacity or add buses.

🔹 passenger_km_proxy(df)

What it shows:
Approximate productivity measure: total passenger load × assumed distance per stop.

Formula:

passenger_km = Σ(load) × 0.8  # 0.8 km assumed stop distance


Interpretation:

Higher → more passenger movement served.

Decline → demand drop or service reduction.

🧭 General Interpretation Notes
Situation	Likely Cause	Recommended Action
High delay + high load	Overcrowding slows buses	Add peak-time buses
High waiting time but low load	Poor scheduling or route mismatch	Redistribute resources
Negative net load	Terminals or low-end data	Ignore unless frequent
Flat heatmap (no peaks)	Even demand	Stable route
Up-high morning & down-high evening	Classic commuter corridor	Maintain bidirectional balance
Many overcrowded trips	Insufficient capacity	Upgrade fleet or increase frequency