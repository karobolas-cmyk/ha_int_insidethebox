DOMAIN = "insidethebox"

CONF_TOKEN = "token"

# Stored in entry.data
CONF_WEBHOOK_ID = "webhook_id"
CONF_WEBHOOK_SECRET = "webhook_secret"

API_BASE = "https://api.insidethebox.se/iotapi"

# Webhook security header (sent by ITB via customHeaders, validated by HA webhook handler)
WEBHOOK_HEADER_NAME = "X-ITB-Webhook-Secret"

# HA event fired on each webhook call
WEBHOOK_EVENT_NAME = "insidethebox_webhook"

# Polling fallback
DEFAULT_SCAN_INTERVAL = 300  # seconds
DEFAULT_OPEN_DURATION = 15   # seconds (0..25 supported by API)