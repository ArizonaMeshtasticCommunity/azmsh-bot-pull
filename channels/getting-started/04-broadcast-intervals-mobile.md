# Recommended Broadcast Intervals in Configuration Settings

These values are the recommeded broadcasting intervals for the various modules that send information out to the Mesh. They are broke down into **Mobile** and **Stationary Nodes**. Please use these recommended settings to keep the network healthy and reduce the possibility of packet collisions.

# Mobile Nodes
## Device (Settings > Device)  
* **Node Info Broadcast Seconds**: **43200/12hours** (0 is default of 3 hours)  
## Position (Settings > Position)  
* **Smart Broadcast**: **ON** (default is ON)  
* **Smart Broadcast Minimum Distance**: **100m** (0 is default of 100 meters)  
* **Smart Broadcast Minimum Interval**: **60/1min** (0 is default of 30 seconds)  
### If GPS is Enabled  
* **Position Broadcast Interval**: **3600/1hour** (0 is default of 60 seconds / 1 hour)  
* **GPS Update Interval**: **300/5min** (0 is default of 120 seconds / 2 minutes)  
## Telemetry (Settings > Module Configuration > Telemetry) (If enabled)  
* **Broadcast Device Metrics**: **3600/1hour** (0 is default of 1800 seconds / 30 minutes)  
* **Device Metrics Update Interval**: **3600/1hour** (0 is default of 1800 seconds / 30 minutes)  
* **Environment Metrics Update Interval**: **3600/1hour** (0 is default of 1800 seconds / 30 minutes)  
* **Power Metrics Update Interval**: **3600/1hour** (0 is default of 1800 seconds / 30 minutes)  
## MQTT (Settings > Module Configuration > MQTT)  
* **Map Report Publish Interval**: **3600/1hour** (0 is default of 3600 seconds / 1 hour) 
## Neighbor Info (Settings > Module Configuration > Neighbor Info)
* **Neighbor Info**: **14400/4hours** (Default is 14400 seconds / 4 hours)
