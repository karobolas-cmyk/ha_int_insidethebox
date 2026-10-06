# Inside The Box – Home Assistant (HACS)

![Inside The Box](./images/insidethebox.png)

> ⚠️ **Experimental Integration**  
> This integration is under development.  
> APIs, entities and behavior may change without notice. Use at your own risk.

---

## 🏠 What is this for?

This integration connects Home Assistant to **Inside The Box** smart parcel box systems.

Official product website:  
👉 https://insidethebox.se/

This integration is intended for users who own an Inside The Box lock system.

---

## ⚠️ Important: Gateway Required for Control

You **must have the official Inside The Box Gateway installed and online** in order to:

- 🔓 Open the lock
- 🔒 Close the lock
- Receive real-time webhook updates

If you do **not** have a gateway:

- The integration will work in **read-only mode**
- You can view lock information (battery, state, accessibility, etc.)
- You **cannot** control (open/close) the lock via API

If the gateway is missing or offline, the API will return: HTTP 422 Unprocessable Entity

---

## ✨ Features

- UI setup (Config Flow)
- API token authentication
- Webhook-based real-time updates
- Polling fallback
- Lock entity
- Battery sensor
- Accessibility sensor
- Gateway status sensor
- Event fired on webhook:
  - `insidethebox_webhook`
- Service:
  - `insidethebox.reregister_webhooks`

---

## 📦 Requirements

- Home Assistant 2026.2.0 or newer
- Inside The Box API token
- An active Home Assistant Cloud (Nabu Casa) connection, or an externally reachable HTTPS URL configured in Home Assistant
  - Settings → System → Network → External URL (for installations without Nabu Casa)

---

## 🚀 Installation (HACS)

1. HACS → Integrations → ⋮ → Custom repositories
2. Add this repository URL
3. Category: **Integration**
4. Install “Inside The Box”
5. Restart Home Assistant

---

## 🔧 Configuration

1. Settings → Devices & Services → Add Integration
2. Search for **Inside The Box**
3. Enter your API token

---

## 🔄 Webhook Notes

When Home Assistant Cloud is available, the integration uses a Nabu Casa cloudhook. No inbound port forwarding or external URL setting is required for that route. If the cloud connects after integration startup, registration is retried when it connects.

Webhook registrations are reused when their destination and secret match, avoiding duplicate notifications after restarts. Incoming requests still require the shared secret. New registrations send it in the HTTPS query string because the API returned HTTP 500 when `customHeaders` was included; existing header-based callers remain supported. Treat the complete webhook URL as a credential and avoid sharing or logging it.

### Last mail timestamp for automations

`YGM` (You Got Mail) arrives as an `insidethebox_webhook` event with `eventType: YGM`. Opening the lock is a separate operation and should not be used as proof that mail was delivered.

Add the following item to your existing `template:` configuration, replacing `YOUR_LOCK_ID` with the lock ID returned by the API. The trigger-based timestamp is restored across restarts and remains unknown until the first matching mail event. It records the time Home Assistant received the event; past deliveries are not recovered by polling.

```yaml
template:
  - triggers:
      - trigger: event
        event_type: insidethebox_webhook
        event_data:
          eventType: YGM
    conditions:
      - condition: template
        value_template: "{{ trigger.event.data.get('lock', {}).get('lockid') == 'YOUR_LOCK_ID' }}"
    sensor:
      - name: "Mailbox last mail"
        unique_id: insidethebox_last_mail
        device_class: timestamp
        icon: mdi:mailbox
        state: "{{ trigger.event.time_fired.isoformat() }}"
```

Use changes to this timestamp sensor as the trigger for your mail automations.


If your external URL changes, run: insidethebox.reregister_webhooks


from Developer Tools → Services.

---

## 🧪 Troubleshooting

### Lock cannot be controlled (422 error)

Check:

- Gateway is installed and ONLINE
- Lock `state` is `ACTIVE`
- `lockAccessibilityState` is `ACCESSIBLE`
- Battery level is not critically low

If control works in the official app but not via API, verify that:

- The gateway is linked to the same account as the API token
- The API token has proper access

---

## 📜 Disclaimer

This project is not affiliated with Inside The Box.

Use at your own risk.

---

## 📄 License

Apache 2.0
