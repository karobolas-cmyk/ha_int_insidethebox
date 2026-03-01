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
- External URL configured in Home Assistant
  - Settings → System → Network → External URL
- Reverse proxy must forward headers (required for webhook security)

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
