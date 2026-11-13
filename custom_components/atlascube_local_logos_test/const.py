DOMAIN = "atlascube_local_logos_test"
PLATFORMS = ["sensor"]
LOGO_DIR = "atlascube-radio-station-logos-test"
COVER_DIR = "atlascube-radio-covers-test"
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_COVER_BYTES = 700 * 1024
WS_GET = f"{DOMAIN}/get"
WS_SAVE = f"{DOMAIN}/save"
WS_LIST = f"{DOMAIN}/list"
WS_DELETE = f"{DOMAIN}/delete"
WS_REFRESH = f"{DOMAIN}/refresh"
WS_SEARCH = f"{DOMAIN}/search"

TRACK_ENTITY_ID = "sensor.atlascube_radio_tytul_utworu"
