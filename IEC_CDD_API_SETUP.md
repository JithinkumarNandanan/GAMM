# IEC CDD / Smart-enabled API Setup

After IEC has approved your application, you can use the IEC Smart-enabled API for IEC CDD lookups in the enrichment pipeline.

## Single API key (recommended)

If IEC gave you **one API key**, set it and run:

**Windows PowerShell:**
```powershell
$env:IEC_CDD_API_KEY="paste-your-api-key-here"
```

**Then run the app (in the same terminal):**
```powershell
python integrated_pipeline.py --source Data/source --target Data/target
# or
streamlit run streamlit_app.py
```

You should see: `[INFO] IEC CDD API (API key) initialized`

Alternative env name: `IEC_SMART_API_KEY` (same value).

---

## Optional: API base URL

Default is `https://sim-apim.azure-api.net/preprod/v1`. Override only if IEC gave you a different base:

```powershell
$env:IEC_CDD_API_BASE_URL="https://your-base-url/v1"
```

## How it’s used

- Your API key is sent as a **Bearer** token on IEC API requests.
- IEC CDD search is tried **first** when the key is set; if nothing is found, the local IEC CDD library is used.

## OAuth2 (only if you have CLIENT_ID + CLIENT_SECRET)

If IEC gave you two credentials instead of one key:

```powershell
$env:IEC_CDD_CLIENT_ID="your-client-id"
$env:IEC_CDD_CLIENT_SECRET="your-client-secret"
```

## References

- [IEC Smart-enabled API – Getting started](https://api.smart.iec.ch/getting-started)
- [Accessing the API (OAuth2)](https://api.smart.iec.ch/access-api)  
  - Token: `POST https://auth.smart.iec.ch/realms/iec/protocol/openid-connect/token`  
  - Body: `client_id`, `client_secret`, `grant_type=client_credentials`, `scope=openid`
- Support: **smart.support@iec.ch** or **helpdesk@iec.ch**
