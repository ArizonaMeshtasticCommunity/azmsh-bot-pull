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
