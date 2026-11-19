# Beginner FAQ

# General
## What is Meshtastic?
* Meshtastic is an open-source project that lets small radios communicate directly with each other over long distances without relying on cell service or the internet. Messages hop from node to node, forming a mesh network.
## What is the Arizona Meshtastic Community?
* We’re a group of people building and supporting a shared Meshtastic network across Arizona. The goal is better coverage, shared knowledge, and a network that works well for everyone.
## Do I need a license to use Meshtastic?
* No. Meshtastic operates on unlicensed ISM bands. No HAM license is required.
## Is Meshtastic only for emergencies?
* No. While it can be useful during emergencies, most people use Meshtastic for experimentation, learning, and general communication.

# Getting Started
## What hardware do I need?
* You need a Meshtastic-compatible LoRa device and a phone or computer to configure it.
## Do I need to be technical to get started?
* Not at all. You can start with basic settings and learn as you go. The community is happy to help.
## What settings should I use for Arizona?
* Settings depend on location. Phoenix and Tucson metro areas use different presets than rural areas. See **[Device Settings & Roles](https://discord.com/channels/1270431345734062133/1274440386827255849/1451257227594829926)** for current recommendations.
## Can I use the default Meshtastic settings?
* Sometimes. Defaults may work in rural areas, but Phoenix and Tucson use modified settings to keep the network stable.

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

# Privacy & Safety
## Are my messages encrypted?
* Yes. Meshtastic encrypts messages on the mesh.
## What information is shared publicly?
* Only basic network and diagnostic information may be visible. Private messages and personal data are not exposed.
## Is my location visible to others?
* Location sharing depends on your settings and can be adjusted or disabled.

# Community
## How can I help the network?
* Run a node, place it thoughtfully, share feedback, and help others get started.
## Who do I contact if I have a problem?
* Ask in Discord, post in **[i-need-help](https://discord.com/channels/1270431345734062133/1358143621362352348)**, or reach out to a community member.
## Are there rules for deploying nodes?
* Yes. Some deployments, especially high-impact ones, have guidelines to keep the network healthy and fair.
