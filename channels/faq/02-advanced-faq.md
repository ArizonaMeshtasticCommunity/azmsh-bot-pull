# Advanced FAQ (Power Users)

# Network Behavior & Performance
## Why does my node hear a lot but forward very little?
* This is usually expected behavior. Forwarding depends on timing, role, and whether your node is actually in a useful position for relaying traffic. Hearing packets does not automatically mean your node should rebroadcast them.
## Should I manually tune timing or rebroadcast values?
* No. Timing values are role- and preset-controlled for a reason. Manual tuning often causes packet collisions or instability, especially in dense areas like Phoenix and Tucson.
## Why does Router_Late exist?
* Router_Late helps reduce collisions by intentionally delaying rebroadcast timing. It is useful for high-elevation sites or busy areas where multiple strong routers can interfere with each other.
## Does higher transmit power always improve the network?
* No. More power can increase noise, collisions, and unnecessary airtime usage. Use the lowest power that reliably reaches neighboring nodes.
## Why does my node sometimes stop relaying temporarily?
* Meshtastic adapts to network conditions. Congestion control, backoff behavior, and role-based timing can all temporarily reduce forwarding to protect overall mesh health.

# MQTT & Diagnostics
## Does enabling MQTT change how my node behaves on RF?
* No. MQTT only affects uplinked diagnostic information. It does not change RF behavior, routing decisions, or message timing.
## Why is downlink disabled?
* Downlink can inject unnecessary traffic into the mesh. Keeping it off prevents external systems from influencing RF behavior.
## Why don’t I see my node immediately on dashboards?
* Dashboards rely on periodic diagnostic updates. Delays are normal and expected, especially on low-traffic or newly deployed nodes.

# Deployment & Scaling
## When does a node justify being a Router?
* Only when it has a clear elevation or coverage advantage and is intended to support the wider mesh. Most nodes should not be Routers.
## Can too many routers hurt the network?
* Yes. Overuse of Router roles can increase collisions and reduce overall reliability, especially in metro areas.
## Is it okay to experiment with settings?
* Yes, but experiments should be temporary and intentional. Always revert to recommended settings after testing.
## Why coordinate mountaintop deployments?
* High-impact nodes affect large areas. Coordination prevents overlapping coverage, timing conflicts, and unintended network behavior.
