# Node Role Breakdown
Choosing the right role helps keep the mesh efficient and reliable. Here’s a simple guide based on where your node will live and how it will function.  
## Client
**Best for:** Rooftop home nodes and fixed installations  
**Purpose:** Standard role for sending, receiving, and relaying messages  
**Use when:**  
- A node is roof-mounted at home.  
- The location supports the network but isn’t acting as a major relay.  
## Client_Mute
**Best for:** Anything mobile (backpacks, vehicles, pocket nodes)  
**Purpose:** Sends and receives only; does **not** rebroadcast others' messages  
**Use when:**  
- You have a mobile node that moves constantly and can unintentionally cause routing issues.  
- Running a or serveral, secondary device alongside a better-positioned node (i.e. a client node)   
## Client_Base 
**Best for:** Well-positioned home base stations (attic/roof nodes)  
**Purpose:** Prioritizes rebroadcasting messages from favorited nodes  
**Use when:**  
- Your mobile/indoor nodes need a reliable local relay.  
- You want router-like priority only for your own devices.
## Router
**Best for:** Mountain-top or high-elevation locations  
**Purpose:** Always awake and forwarding traffic  
**Use when:**  
- The node is deployed permanently on a peak.  
- The site has major coverage or elevation advantages.  
## Router_Late
**Best for:** Mountain tops or **experimental rooftop installs**  
**Purpose:** Always rebroadcasts, but delays to let closer nodes respond first  
**Use when:**  
- A deployment sits very high or receives lots of traffic.  
- Testing for improved performance on rooftops.  

**When in doubt, client it out** If you are unsure of the best role to set your devices to, select `client_mute` and talk with a community member to assist you in getting setup correctly.
