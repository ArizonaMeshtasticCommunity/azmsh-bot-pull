# MQTT Settings
If you’d like to help the community capture data in order to optimize the network, you may setup your node for MQTT upload. Here's how...
## MQTT Broker (Uplink Only)
If you want your node’s diag/info to appear on tools like MeshView, Liam Maps, or the Metrics Dashboard, you can enable MQTT within the device MQTT settings, using the Arizona Mestastic Community MQTT broker information below:

- **Server:** {{MQTT_SERVER}}  
- **Username:** {{MQTT_USER}}  
- **Password:** {{MQTT_PASS}}  
## Official Topics
Choose the topic that matches your area. The city or area name should start with a capital letter.
```
msh/US/AZ/Tucson
msh/US/AZ/Mesa
msh/US/AZ/Phoenix
msh/US/AZ/{YourCityOrArea}
```
## LoRa Settings  
There is a setting specific to MQTT within the LoRa settings page that is highly recommended to be turned on. 
- Okay to MQTT
This setting will allow other nodes to pass basic diagnostic info over the mesh to the MQTT broker. 
## Channel Settings.
These settings can be found on the channel settings pages.
- **Uplink:** ON  
- **Downlink:** OFF  
Downlink should remain off to prevent unnecessary traffic on the mesh.
## What MQTT Does (and Doesn't Do)
MQTT helps the community understand how the Meshtastic network is behaving across Arizona by sending **basic diagnostic and status information** from your node to our dashboards. This allows us to spot coverage issues, detect outages, and improve the overall network.
- It is used **only** for troubleshooting and network diagnostics.  
- It does **not** process personal data, private messages, or anything identifying about you.  
- It simply gives us a clearer picture of how the statewide mesh is performing.
Enabling MQTT uplink is optional, but it helps support the Arizona Meshtastic network.
