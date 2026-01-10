# Data Collectors

Collection scripts for the Nexus Risk Platform.

## Usage

### Weather Collector (Every 12 hours)
```bash
python weather_collector.py
```
Collects weather data from 7 waypoints along Taiwan-US route.

### News Collector (Every 6 hours)
```bash
python news_collector.py
```
Fetches news from GDELT for Taiwan Strait, semiconductor, and shipping keywords.

### Port Collector (Weekly manual)
```bash
# Interactive mode
python port_collector.py

# Quick mode
python port_collector.py --quick USLAX 10 2.5 0.7
```
Enter port congestion data manually.

### Scheduler (Background daemon)
```bash
python scheduler.py
```
Runs weather and news collection on schedule.

## Data Targets
| Collector | Frequency | RAM | API Calls |
|-----------|-----------|-----|-----------|
| Weather | 12 hours | ~30MB | 14/day |
| News | 6 hours | ~100MB | 32/day |
| Port | Weekly | <10MB | 4/week |
