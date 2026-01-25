# Rate Limiting Analysis

## Summary

There are **TWO separate APIs** being called, each with different rate limits:

1. **Sefaria API** - Text retrieval (no limits encountered)
2. **Google Gemini API** - AI classification (STRICT 10 req/min limit)

---

## 1. Sefaria API

**What it does:** Fetches Talmud text (Hebrew + English) from Sefaria.org

**Endpoint:** `https://www.sefaria.org/api/texts/{ref}`

**Example:** `https://www.sefaria.org/api/texts/Ketubot 2a`

**Rate Limits:**
- Sefaria is a non-profit with generous API access
- No documented strict rate limits for reasonable use
- Our usage: 1 request per page = 76 requests for Ketubot 2-39
- **No issues encountered with Sefaria API**

**Current code:** No rate limiting applied (not needed)

```python
def get_page_with_segments(ref: str) -> Optional[Dict]:
    url = f"{SEFARIA_API}/texts/{ref}"
    response = requests.get(url, timeout=15)
    # ... process response
```

---

## 2. Google Gemini API

**What it does:** Uses AI to classify whether text contains a story

**Model:** `gemini-2.0-flash-exp` (experimental)

**Rate Limits (STRICT):**
- **10 requests per minute** per model per project
- This is a HARD limit enforced by Google
- Error when exceeded: `429 ResourceExhausted`

**Error Details:**
```
google.api_core.exceptions.ResourceExhausted: 429 You exceeded your current quota
quota_metric: "generativelanguage.googleapis.com/generate_requests_per_model"
quota_id: "GenerateRequestsPerMinutePerProjectPerModel"
quota_value: 10
```

**Google's suggestion:** "migrate to Gemini 2.5 Flash Image for higher quota limits"

**Our usage:**
- 1 AI classification request per page
- 76 pages (Ketubot 2-39) = 76 requests
- At 10 req/min: **Minimum 7.6 minutes** required

---

## Current Rate Limiting Strategy

### v5.1 Code (Updated)

```python
def analyze_tractate_v5(tractate: str, start_page: int = 2, end_page: int = 10):
    for page_num in range(start_page, end_page + 1):
        for side in ['a', 'b']:
            ref = f"{tractate} {page_num}{side}"

            # 1. Fetch from Sefaria (fast, no rate limit)
            page_data = get_page_with_segments(ref)

            # 2. AI classification (rate limited by Google)
            classification_result = classifier.classify_page(ref, page_data['segments'])

            # 3. RATE LIMITING: Wait 7 seconds between pages
            time.sleep(7)  # Gemini 2.0 Flash: 10 req/min = 6s minimum, using 7s for safety
```

**Calculation:**
- 10 requests/minute = 60 seconds / 10 = 6 seconds minimum
- We use **7 seconds** for safety margin
- 76 pages × 7 seconds = **532 seconds = ~9 minutes**

---

## Which API is the Bottleneck?

**Google Gemini API is the ONLY bottleneck:**
- Sefaria API: Fast, no issues
- Google API: HARD 10 req/min limit

**Time breakdown for 76 pages:**
- Sefaria API calls: ~10-20 seconds total (fast, parallel could work)
- Google API calls: **532 seconds = 9 minutes** (FORCED by rate limit)
- Total time: **~9 minutes** (entirely due to Google's limit)

---

## Solutions to Speed Up

### Option 1: Upgrade to Gemini 2.5 Flash (RECOMMENDED)
Google's error message suggests: "migrate to Gemini 2.5 Flash Image for higher quota limits"

**Pros:**
- Higher rate limits
- Newer model
- Same API structure

**Cons:**
- Need to test if model performs as well
- May have different pricing

### Option 2: Use Multiple API Keys
If you have access to multiple Google Cloud projects:
- Each project gets 10 req/min
- 2 projects = 20 req/min = ~3-4 minutes for 76 pages

**Cons:**
- Requires multiple accounts
- More complex code

### Option 3: Switch to Claude API (Anthropic)
Already in codebase (v4 used it):
- Different rate limits (likely higher)
- Different pricing model

**Cons:**
- More expensive per request
- Would need to re-validate accuracy

### Option 4: Accept the 9-minute wait (CURRENT)
- Works reliably
- Simple implementation
- Free tier friendly

---

## Package Update Needed

**Current (Deprecated):**
```python
import google.generativeai as genai  # Version 0.8.6 - DEPRECATED
```

**New (Recommended):**
```python
from google import genai  # Version 1.57.0 - Current
```

**Migration required:** The new package has a different API structure. Need to update:
1. Client initialization
2. Model configuration
3. Response handling

See: https://github.com/google-gemini/deprecated-generative-ai-python

---

## Recommendation

**For immediate use:**
- Keep current 7-second delay (works, reliable)
- 9 minutes for full validation is acceptable

**For future:**
1. Migrate to `google-genai` 1.57.0 (new package)
2. Test Gemini 2.5 Flash for higher rate limits
3. Consider caching results to avoid re-running same pages

---

## Testing Rate Limits

To verify current limits:
```bash
# Check your quota status
curl https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp \
  -H "Authorization: Bearer $(gcloud auth print-access-token)"
```

Or check Google Cloud Console:
https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
