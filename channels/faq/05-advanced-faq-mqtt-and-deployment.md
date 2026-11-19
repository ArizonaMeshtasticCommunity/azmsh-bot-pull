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
