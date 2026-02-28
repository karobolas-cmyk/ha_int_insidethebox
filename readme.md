# Inside The Box – Home Assistant (HACS)

Home Assistant custom integration for **Inside The Box** (api.insidethebox.se).

## Features

- Configured via UI (Config Flow): enter API token
- Uses **Home Assistant Webhook** for push updates (cloud_push)
- Automatically registers a webhook **per lock**
- Exposes:
  - `lock` entities for each ITB lock
  - sensors for battery/accessibility and gateway connection info
- Fires a Home Assistant event on every webhook callback:
  - `insidethebox_webhook` (payload included)
- Includes a service to re-register webhooks:
  - `insidethebox.reregister_webhooks`

## Requirements

- Home Assistant set up with a public **External URL**:
  - Settings → System → Network → **External URL**
- Your reverse proxy (if any) must forward request headers (the integration validates a shared secret header).

## Installation (HACS)

1. HACS → Integrations → ⋮ → **Custom repositories**
2. Add this repository URL, category: **Integration**
3. Install “Inside The Box”
4. Restart Home Assistant

## Configuration

1. Settings → Devices & Services → Add Integration
2. Search for **Inside The Box**
3. Paste your API token (from the Inside The Box app)

The integration will:
- create a webhook endpoint in Home Assistant
- register it to Inside The Box for each lock

If you later change your external URL, run the service:
- Developer Tools → Services → `insidethebox.reregister_webhooks`

## Entities

### Locks
Each lock is exposed as a `lock` entity.

- Locked state is derived from ITB `isLockOpen`:
  - `isLockOpen = true` → entity is **unlocked**
  - `isLockOpen = false` → entity is **locked**

### Sensors
- Lock:
  - Battery level
  - Accessibility state
- Gateway:
  - Connection status
  - Connection changed timestamp

## Automations (webhook event)

Example: notify on “You Got Mail” events:

```yaml
alias: ITB - You Got Mail
trigger:
  - platform: event
    event_type: insidethebox_webhook
condition:
  - condition: template
    value_template: "{{ trigger.event.data.eventType == 'YGM' }}"
action:
  - service: notify.notify
    data:
      message: "You got mail (Inside The Box)."