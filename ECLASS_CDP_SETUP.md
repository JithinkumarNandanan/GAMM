# eCl@ss CDP Webservice Setup

## Two types of eCLASS access

| Type | What it is | How this project uses it |
|------|------------|---------------------------|
| **Library download** | Full eCLASS release (e.g. 15.0) as files from the ECLASS shop. You already have this for your thesis. | Place the eCLASS XML/JSON dictionary files in the **`EClass`** folder (or set `eclass_folder`). The app loads them and uses them for semantic enrichment—**no API key needed**. |
| **CDP Webservice** | REST API at [eclass-cdp.com](https://www.eclass-cdp.com/) for on-demand queries (by IRDI or search). | Optional. Requires a **certificate or token** from ECLASS (separate from library download). If set via `ECLASS_CDP_API_KEY`, the app calls the API first, then falls back to local library. |

**If you only have library download access:** You can use the app as-is with the eCLASS 15.0 files in the `EClass` folder. CDP API setup below is only needed if you later get Webservice/certificate access.

---

## ECLASS IRDI (International Registration Data Identifier)

ECLASS uses globally unique identifiers (IRDIs) based on ISO/IEC 11179-6, ISO 29002 and ISO/IEC 6523. Structure:

| Part | Meaning | Example |
|------|--------|--------|
| **ICD + OI** | International Code Designator + Organization Identifier (ISO/IEC 6523). ECLASS = 0173; others: ISO 0112, ODETTE 0177, SIEMENS 0175, GTIN 0160. | 0173 |
| **CSI** | Code Space Identifier (ISO 29002-5). Type of object. | see table below |
| **Concept code** | 6-digit identifier | e.g. AAR710 |
| **Version** | Version of the object | e.g. 003 |

**Code Space Identifiers (CSI) used in ECLASS XML:**

| CSI | Category | Used in ECLASS XML |
|-----|----------|--------------------|
| 01 | class | YES |
| 02 | property | YES |
| 05 | unit of measure | YES |
| 07 | property value | YES |
| 09 | data type | YES |
| 11 | ontology | YES |
| Z2 | aspect of conversion | YES |
| Z3 | template | YES |
| Z4 | quantity | YES |
| Z5 | keywords | YES |
| Z6 | synonyms | YES |

**Example IRDI:** `0173-1#02-AAR710#003` → ICD/OI 0173-1, CSI 02 (property), concept AAR710, version 003.

**Company-specific ranges (concept code):** X = user-specific, Y = manufacturer-specific, Z = ECLASS-internal. ECLASS does not use X or Y so company-specific elements are not replaced by standard ones.

---

## ECLASS XML Read Service (v2)

CDP exposes the **XML Read Service** under `/xmlapi/v2/`. Use IRDI in **path form** (hyphens): `0173-1-02-AAS574-002`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/xmlapi/v2/classes` | All first-level Classification Classes (segments) |
| GET | `/xmlapi/v2/classes/{codedName}` | Retrieve a class by coded name |
| GET | `/xmlapi/v2/classes/{irdi}` | Retrieve a class by IRDI |
| GET | `/xmlapi/v2/classifiedAs/{irdi}` | List of Classification Classes assigned to Application Class |
| GET | `/xmlapi/v2/properties/{irdi}` | Retrieve a Property |
| GET | `/xmlapi/v2/units/{irdi}` | Retrieve a Unit |

**Examples (XML V2):**
- With resource path: `https://eclass-cdp.com/xmlapi/v2/properties/0173-1-02-AAS574-002`
- Direct path (api host): `https://api.eclass-cdp.com/0173-1-02-AAC895-008`

Base URL can be `https://www.eclass-cdp.com` or `https://api.eclass-cdp.com` depending on your license; use `ECLASS_CDP_BASE_URL` and avoid following redirects to the portal (see "Base URL and avoiding the portal" below).

---

### Using your eCLASS 15.0 library download (what you have now)

1. Download the eCLASS 15.0 release from the ECLASS shop (using the access granted for your thesis).
2. Place the XML (or JSON) dictionary files in a folder, e.g. `EClass`, in this project.
3. Run the app—it will load those files automatically and use them for semantic matching. No `ECLASS_CDP_API_KEY` is required.

---

## How to use your eClass web service license

If you received a **license file** or **token** for the eCl@ss CDP Webservice, use one of the options below.

### Option A: License file (recommended)

1. **Put the token in a file**  
   - If ECLASS gave you a text file with a token/key, you can use it as-is.  
   - If you received a string (e.g. by email), create a text file and paste the token as the first line, e.g. in:
     - `EClass/API License/token.txt`  
     - or `EClass/cdp_token.txt`  
   - The file should contain **only the token** (no extra text); the first line is used.

2. **Point the app at the file**  
   Set the environment variable to the **path** of that file (absolute or relative to the project folder):

   **Windows PowerShell (current session):**
   ```powershell
   $env:ECLASS_CDP_API_KEY = "EClass/API License/token.txt"
   ```
   Or with full path:
   ```powershell
   $env:ECLASS_CDP_API_KEY = "D:\Thesis\template\EClass\API License\token.txt"
   ```

3. **Run the app** (in the same terminal where you set the variable):
   ```powershell
   streamlit run streamlit_app.py
   # or
   python integrated_pipeline.py --source "Data/AAS Data" --target "Data/AAS Data"
   ```
   You should see: `[INFO] eCl@ss CDP Webservice API enabled`.

### Option B: Token in environment (no file)

Set the **token string** directly:

**Windows PowerShell:**
```powershell
$env:ECLASS_CDP_API_KEY = "your-actual-token-here"
```
Then run the app in the same terminal.

### Option C: You only have the files in `EClass/API License/` (e.g. `.full.pem` and `.public.key`)

If your folder contains only:
- **204-SimPlan_Webservice.full.pem**
- **204-SimPlan_Webservice.public.key**

then use the **`.full.pem`** file only. It already contains both the certificate and the private key, so you do **not** need the `.public.key` file for the API.

**PowerShell (run in the same terminal as the app):**
```powershell
$env:ECLASS_CDP_KEY = "EClass/API License/204-SimPlan_Webservice.full.pem"
streamlit run streamlit_app.py
```

Or with full path:
```powershell
$env:ECLASS_CDP_KEY = "D:\Thesis\template\EClass\API License\204-SimPlan_Webservice.full.pem"
python integrated_pipeline.py --source "Data/AAS Data" --target "Data/AAS Data"
```

You should see: `[INFO] eCl@ss CDP Webservice API enabled`. The app uses the `.full.pem` as both certificate and key for TLS client authentication.

---

### Option D: .key file (separate certificate and private key)

eClass CDP can use **TLS client certificate** authentication. You need:

1. **Private key file** (e.g. `something.key`) — the `.key` file you received.  
   **Important:** Use your **private** key file, not a `.public.key` file (the public key cannot authenticate the client).

2. **Certificate file** (e.g. `.crt`, `.pem`, or `.cer`) — often sent together with the key, or you may already have e.g. `204-SimPlan_Webservice.full.pem` in `EClass/API License/`.

**Steps:**

1. Put both files in the same folder, e.g. `EClass/API License/`:
   - Your private key: e.g. `EClass/API License/204-SimPlan_Webservice.key` (or whatever your `.key` file is named).
   - The certificate: e.g. `EClass/API License/204-SimPlan_Webservice.full.pem` (or `*.crt` / `*.pem` in that folder).

2. Set **only** the key path (the app will look for the cert in the same folder if you don’t set it):

   **Windows PowerShell:**
   ```powershell
   $env:ECLASS_CDP_KEY = "EClass/API License/204-SimPlan_Webservice.key"
   ```
   If your cert has a different name, set it explicitly:
   ```powershell
   $env:ECLASS_CDP_CERT = "EClass/API License/204-SimPlan_Webservice.full.pem"
   $env:ECLASS_CDP_KEY = "EClass/API License/204-SimPlan_Webservice.key"
   ```

3. Run the app in the same terminal:
   ```powershell
   streamlit run streamlit_app.py
   ```
   You should see: `[INFO] eCl@ss CDP Webservice API enabled`.

**Auto-detection:** If you set only `ECLASS_CDP_KEY`, the code looks for a certificate in the same directory: same base name with `.crt`, `.pem`, or `.cer`, or any file named `*.full.pem`.

### Option E: .env file (keeps token out of the shell)

1. Create a file named `.env` in the project root (e.g. `d:\Thesis\template\.env`).
2. Add one line (replace with your token or path to license file):
   ```
   ECLASS_CDP_API_KEY=your-token-here
   ```
   or for certificate auth:
   ```
   ECLASS_CDP_KEY=EClass/API License/yourfile.key
   ECLASS_CDP_CERT=EClass/API License/yourfile.full.pem
   ```
3. Load it before running: e.g. `pip install python-dotenv` and add `from dotenv import load_dotenv; load_dotenv()` at the top of `streamlit_app.py` or run your script with a wrapper that loads `.env`.

---

**Summary**

| What you have | What to do |
|---------------|------------|
| **Token string** | Set `ECLASS_CDP_API_KEY` to that string (env or .env). |
| **License file with token** | Put the token in a file (e.g. `EClass/API License/token.txt`), set `ECLASS_CDP_API_KEY` to the **path** of that file. |
| **Only files in `EClass/API License/`** (e.g. `204-SimPlan_Webservice.full.pem` + `.public.key`) | Set `ECLASS_CDP_KEY` to the path of the **`.full.pem`** file. That file contains both cert and private key; the app uses it for client certificate auth. You do not need the `.public.key` file. |
| **.key file (private key) + separate cert** | Put the `.key` and certificate in `EClass/API License/`. Set `ECLASS_CDP_KEY` to the `.key` path; set `ECLASS_CDP_CERT` if the cert has a different name. |

**Other optional env vars:**
- `ECLASS_CDP_TOKEN` – alternative to `ECLASS_CDP_API_KEY` (same meaning).
- `ECLASS_CDP_CERT` – path to certificate file (only needed when using `.key` if the cert filename is not auto-detected).
- `ECLASS_CDP_BASE_URL` – default is `https://www.eclass-cdp.com`. Change only if ECLASS gives you another base URL.

### Base URL and avoiding the portal

If you see requests going to `eclass-cdp.com/portal/seam/resource/rest/dictionary/...`, that is the **portal** path. The app does **not** build that path; it comes from the server redirecting. To avoid it:

1. **Use the API host:** set `ECLASS_CDP_BASE_URL=https://api.eclass-cdp.com`. The app will then call only direct URLs like `https://api.eclass-cdp.com/0173-1-02-AAR710-003` and will not use `/xmlapi/v2/...` or any path that might redirect to the portal.
2. **Redirects are disabled:** all CDP requests use `allow_redirects=False`, so the client never follows a redirect to `portal/seam/...`. If the server returns 302 to the portal, you get the redirect response (e.g. 302) and no body—switching to `api.eclass-cdp.com` usually fixes that.

### Skipping the API (default)

By default the **pipeline skips the eClass CDP API** and uses only local eClass files (faster, no network calls). The pipeline report includes **eclass_cdp_api: skipped (local files used)**.

To **enable** the API (e.g. for lookups by IRDI or when local files are missing), set:
```powershell
$env:ECLASS_CDP_SKIP_API = "0"
```
Then run the pipeline or Streamlit app in the same terminal.

## How to check that it works

1. **Set your certificate** (same terminal you use below):
   ```powershell
   $env:ECLASS_CDP_KEY = "EClass/API License/204-SimPlan_Webservice.full.pem"
   ```

2. **Run the check script** from the project root:
   ```powershell
   python check_eclass_cdp.py
   ```
   You should see:
   - `Auth: Client certificate` (or Bearer token)
   - `OK (status 200, ...)` for GET /xmlapi/v2/classes
   - Optionally a property fetched by IRDI
   - `eClass CDP check finished: connection works.`

   If you see **401 Unauthorized**, the certificate is not accepted (wrong file, expired, or not for CDP). If you see **Not configured**, set `ECLASS_CDP_KEY` (or `ECLASS_CDP_API_KEY`) in the same terminal before running the script.

3. **Or run the app** and look for the message when enrichment loads:
   ```powershell
   streamlit run streamlit_app.py
   ```
   In the terminal you should see: `[INFO] eCl@ss CDP Webservice API enabled`. Then run a pipeline or use the app to enrich nodes; if nodes have eClass IRDIs, the app will use the CDP XML API to fetch definitions and units.

## Requesting a description by IRDI

To get the **description** (and unit, value type) for a parameter when you have its **eClass IRDI**:

1. **Set your certificate** (same terminal):
   ```powershell
   $env:ECLASS_CDP_KEY = "EClass/API License/204-SimPlan_Webservice.full.pem"
   ```

2. **Run the helper script** with the IRDI:
   ```powershell
   python get_eclass_description_by_irdi.py 0173-1#02-AAY070#001
   ```
   Or with hyphen form:
   ```powershell
   python get_eclass_description_by_irdi.py 0173-1-02-AAR710-003
   ```

   The script prints **Description**, **Unit**, and **Value type** for that parameter.

3. **From your own code** you can call:
   ```python
   from enrichment_module import get_eclass_description_by_irdi
   result = get_eclass_description_by_irdi("0173-1#02-AAY070#001")
   if result:
       print(result["definition"])  # description
       print(result["unit"])
       print(result["value_type"])
   ```

   `result` is a dict with keys: `definition`, `usage`, `unit`, `value_type`, `eclass_id`. The API used is the eClass CDP XML Read Service (GET property by IRDI).

## How the app uses the CDP

With CDP configured (certificate or token), the app uses the eClass CDP API so that **target (and source) nodes are enriched from the API instead of searching through local eClass XML files** when possible:

1. **Value is a full CDP URL** – If a node’s `value` is a URL like `https://api.eclass-cdp.com/0173-1-02-AAR710-003` (or `https://www.eclass-cdp.com/...`), the app **calls that URL** with your certificate, parses the XML response, and uses it for definition, unit, and value type. No local eClass folder search is done for that node.
2. **Value or metadata contains an eClass IRDI** – If the node has an IRDI (e.g. `0173-1#02-AAY070#001`) in metadata or in `value`, the app calls **GET /xmlapi/v2/properties/{irdi}** (on the base URL you configured) and uses the result.
3. **Otherwise** – The app falls back to searching the local eClass XML files in the `EClass` folder.

So for target AAS files where semantic IDs or values are set to eClass CDP URLs (e.g. `https://api.eclass-cdp.com/0173-1-02-AAR710-003`), the pipeline will use the API to retrieve parameter information instead of scanning the eClass folder.

**Optional:** Set `ECLASS_CDP_BASE_URL` to `https://api.eclass-cdp.com` (or keep default `https://www.eclass-cdp.com`) if your license uses the API subdomain. URL-based values in nodes are used as-is (same cert is sent to api.eclass-cdp.com or www.eclass-cdp.com).

## API references

- **XML V1:** [SwaggerHub – ECLASS Download XML 1.0.4](https://app.swaggerhub.com/apis-docs/ECLASS_Standard/ECLASS_Download_XML/1.0.4)  
- **XML V2:** [SwaggerHub – ECLASS Download XML 2.0.0](https://app.swaggerhub.com/apis-docs/ECLASS_Standard/ECLASS_Download_XML/2.0.0)  
- **JSON V1:** [SwaggerHub – ECLASS Download JSON 1.4.2](https://app.swaggerhub.com/apis-docs/ECLASS_Standard/ECLASS_Download_JSON/1.4.2)  
- **JSON V2:** [SwaggerHub – ECLASS Download JSON 2.0.4](https://app.swaggerhub.com/apis-docs/ECLASS_Standard/ECLASS_Download_JSON/2.0.4)  
- Base URL for CDP: **https://www.eclass-cdp.com/**

---

# Email draft: Request free certificate for thesis

Use the text below (or adapt it) to request a **free certificate for academic/thesis use** from ECLASS. Send to **meissner-peters@eclass-office.com** (or the contact on [eclass.eu](https://eclass.eu)).

---

**Subject:** Request for free eCl@ss CDP Webservice certificate for academic thesis

Dear Ms. Meißner-Peters / ECLASS team,

I am a master’s student at Otto-von-Guericke-University Magdeburg (M.Sc. Systems Engineering for Manufacturing) writing my thesis on semantic data mapping and interoperability between industrial data standards, including Asset Administration Shells and eCl@ss. The thesis is titled **"Generalized Methodology for Automated Mapping of Model Parameters to Asset Administration Shell (AAS) Submodels"** and is supervised by Prof. Dr.-Ing. habil. Arndt Lüder, in collaboration with SimPlan AG.

I already have download access to the eCLASS 15.0 library for this research (thank you again for granting it). For my prototype I would additionally like to use the **eCl@ss CDP Webservice** (REST API) to access structure elements (e.g. classes and properties) on demand, rather than only the full release files.

I have read that the CDP Webservice requires a certificate, which can be acquired through the ECLASS Shop. I would like to ask whether it is possible to obtain a **free certificate or token for academic/thesis use** so that I can integrate the Webservice (XML or JSON API) into my research prototype for non-commercial purposes only.

Could you please let me know the procedure and any conditions for such an academic access?

Thank you for your support.

Best regards,  
Jithinkumar Nandanan  
M.Sc. Systems Engineering for Manufacturing  
Otto-von-Guericke-University Magdeburg  
jithinkumar.nandanan@st.ovgu.de  

---

**Note:** If ECLASS provides a **client certificate** (e.g. `.pem`/`.crt` + key) instead of a simple token, authentication may need to be configured in the application (e.g. `requests` with `cert=` and `key=`). The current code supports a **Bearer token** in `ECLASS_CDP_API_KEY`; if you receive only a certificate file, we can add client-certificate support in a follow-up step.
