# Network & Use
## How far does Meshtastic work?
* Range varies widely. In cities, it may be a few miles. With good elevation and clear paths, nodes can communicate tens or even hundreds of miles.
## Can I send private messages?
* Yes. Meshtastic supports encrypted direct messages.
## What is MQTT and do I need it?
* MQTT is optional. It helps the community understand and troubleshoot the network using basic status info. It does not handle private messages.
## Why don’t my messages always go through?
* Mesh networks depend on placement, timing, and conditions. Terrain, interference, and network load all play a role.

# Nodes & Deployment
## Can I put up a node on a mountain or tower?
* Not without coordination. High-impact deployments should be discussed with the community first.
## What role should my node use?
* That depends on where the node is and whether it moves. Mountain-top, rooftop, and mobile nodes use different roles. See **[Node Role Breakdown](https://discord.com/channels/1270431345734062133/1274440386827255849/1451266215246041321)**.
## Can I run multiple nodes?
* Yes. Many people run multiple nodes for different purposes.
## Why shouldn’t mobile nodes relay traffic?
* Mobile nodes move constantly and can cause routing instability. Using `Client_Mute` helps keep the mesh stable.
