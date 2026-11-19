# AZMSH Discord Posts as Code (`azmsh-bot-pull`)

Authoritative source of truth for static Arizona Meshtastic Community Discord channels, synced via the [`posts_as_code`](https://github.com/ArizonaMeshtasticCommunity/Meshtastic-Cogs) Red-DiscordBot cog.

## Directory Structure

```text
channels/
├── rules/              → #rules
├── getting-started/    → #getting-started
├── leadership/         → #leadership
└── faq/                → #faq
```

Files inside each folder are sorted alphabetically (case-insensitive) and posted in order. Supported formats:
- Markdown: `.md` (Discord bot limit is **2,000 characters** per message; longer files trigger a split confirmation prompt on sync)
- Standalone images: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`

## Template Variables

Credentials and Discord-only settings are stored in Redbot rather than committed to Git, using `{{VAR_NAME}}` placeholders:

| Variable | Used In |
|----------|---------|
| `{{METRO_PRESET}}` | `channels/getting-started/01-device-settings-and-roles.md` |
| `{{METRO_FREQ_SLOT}}` | `channels/getting-started/01-device-settings-and-roles.md` |
| `{{MQTT_SERVER}}` | `channels/getting-started/03-mqtt-settings.md` |
| `{{MQTT_USER}}` | `channels/getting-started/03-mqtt-settings.md` |
| `{{MQTT_PASS}}` | `channels/getting-started/03-mqtt-settings.md` |
| `{{GRAFANA_PASS}}` | `channels/getting-started/06-community-links.md` |

## Bot Setup Commands

```text
[p]pac repo https://github.com/ArizonaMeshtasticCommunity/azmsh-bot-pull.git main
[p]pac token <fine-grained-read-only-pat>

[p]pac var set METRO_PRESET <value>
[p]pac var set METRO_FREQ_SLOT <value>
[p]pac var set MQTT_SERVER <value>
[p]pac var set MQTT_USER <value>
[p]pac var set MQTT_PASS <value>
[p]pac var set GRAFANA_PASS <value>

[p]pac map #rules channels/rules
[p]pac map #getting-started channels/getting-started
[p]pac map #leadership channels/leadership
[p]pac map #faq channels/faq

[p]pac diff
[p]pac sync
```
