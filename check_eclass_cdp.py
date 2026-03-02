import os
import requests

def irdi_to_path(irdi: str) -> str:
    """Convert eClass IRDI to URL path form for direct API.
    IRDI = ICD/OI (e.g. 0173) + CSI (01=class, 02=property, 05=unit) + concept code + version.
    Example: 0173-1#02-AAR710#003 -> 0173-1-02-AAR710-003."""
    if not irdi or not isinstance(irdi, str):
        return ""
    return irdi.strip().replace("#", "-")

# 1. Configuration – use env so same as rest of app; direct API base for correct data
CERT_PEM_PATH = os.getenv(
    "ECLASS_CDP_KEY",
    r"D:\Thesis\template\EClass\API License\204-SimPlan_Webservice.full.pem",
)
BASE_URL = os.getenv("ECLASS_CDP_BASE_URL", "https://api.eclass-cdp.com").rstrip("/")

# 2. IRDI (hash or hyphen form) – normalized to path for direct API
irdi = "0173-1#02-AAR710#003"  # or "0173-1-02-AAC895-008"
path_irdi = irdi_to_path(irdi)
api_endpoint = f"{BASE_URL}/{path_irdi}"

try:
    # 3. Direct path + correct Accept + no redirects => correct ECLASS XML data
    response = requests.get(
        api_endpoint,
        cert=CERT_PEM_PATH,
        headers={
            "Accept": "application/x.eclass.v5+xml",
            "Accept-Language": "en-US",
        },
        allow_redirects=False,
        timeout=15,
    )
    response.raise_for_status()

    # 4. Result is ECLASS XML (property/class definition)
    print("Request successful (direct API path).")
    print(f"URL: {api_endpoint}")
    print(response.text[:500])

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
except Exception as err:
    print(f"An error occurred: {err}")