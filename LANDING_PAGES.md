# Meta Ads Landing Pages

This document describes the five Meta (Facebook/Instagram) advertising landing pages built for Accelerated Rehab Therapy, including their technical implementation, URL structure, lead routing, and activation steps.

---

## Overview

These landing pages are purpose-built for paid ad campaigns targeting chronic pain, shockwave therapy, plantar fasciitis, tendon injuries, and non-surgical rehab patients in the Greeley and Denver markets.

**Key design decisions:**
- Stripped-down layout — logo-only header, no main navigation, minimal footer — to eliminate exit points and keep visitors focused on the lead form
- Mobile-first — sticky dual-call bar pinned to the bottom of the screen on mobile devices
- Each page has its own URL and Meta Pixel PageView event; the shared `/thank-you/` page fires a `Lead` conversion event
- Leads are stored in the database and trigger email notifications routed by preferred location

---

## Landing Pages

| Page | URL | Campaign Target |
|------|-----|-----------------|
| Shockwave Therapy Denver | `/shockwave-therapy-denver/` | Chronic pain / Denver market |
| Shockwave Therapy Greeley | `/shockwave-therapy-greeley/` | Chronic pain / Greeley market |
| Shockwave Therapy for Plantar Fasciitis | `/shockwave-therapy-plantar-fasciitis/` | Heel pain sufferers |
| Chronic Tendon Pain Treatment | `/chronic-tendon-pain-treatment/` | Athletes / active adults |
| Non-Surgical Pain Relief Denver | `/non-surgical-pain-relief-denver/` | Broad chronic pain / Denver |
| Thank You (confirmation) | `/thank-you/` | Post-submission (all campaigns) |

None of these pages are linked in the main site navigation or sitemap — they are reachable only via ad traffic.

---

## Lead Form Fields

Every landing page includes the same lead capture form:

| Field | Type | Required |
|-------|------|----------|
| Full Name | Text | Yes |
| Phone Number | Tel | Yes |
| Email Address | Email | Yes |
| Condition / Reason for Visit | Text | No |
| Preferred Location | Select (Greeley / Denver / No preference) | No |

A hidden `source_page` field records which landing page the lead came from.

---

## Lead Storage

Every form submission creates a `LandingPageLead` record in the database, viewable in the Django admin at:

```
/admin/main/landingpagelead/
```

The admin interface supports:
- Filtering by source page, preferred location, and date submitted
- Searching by name, email, phone, or condition
- Sorting by submission date (newest first)

---

## Email Notification Routing

Every lead sends email notifications to multiple recipients based on the patient's preferred location.

| Preferred Location | Recipients |
|--------------------|------------|
| Greeley | `casemanager.art@gmail.com` + `greeleyrehab@gmail.com` |
| Denver | `casemanager.art@gmail.com` + `artdenver.art@gmail.com` |
| No preference | `casemanager.art@gmail.com` + `greeleyrehab@gmail.com` + `artdenver.art@gmail.com` |

The primary inbox (`casemanager.art@gmail.com`) receives every lead regardless of location.

These addresses are configured in `settings.py` via environment variables, making them easy to update without touching code:

```
LEAD_EMAIL_PRIMARY=casemanager.art@gmail.com
LEAD_EMAIL_GREELEY=greeleyrehab@gmail.com
LEAD_EMAIL_DENVER=artdenver.art@gmail.com
```

Add or update these in your `.env` file to change the routing.

---

## Meta Pixel Integration

The Pixel is wired but inactive until a Pixel ID is provided.

**To activate:**

1. Create a Pixel in [Meta Business Manager](https://business.facebook.com) → Events Manager → Connect Data Sources → Web → Meta Pixel
2. Copy the Pixel ID (a 15–16 digit number)
3. Add it to your `.env` file:
   ```
   META_PIXEL_ID=your_pixel_id_here
   ```
4. Deploy — no code changes required

**Events tracked:**
- `PageView` — fires on every landing page load
- `Lead` — fires on the `/thank-you/` page after a successful form submission

Since each landing page has a unique URL, Meta Ads Manager can attribute conversions to the correct campaign, ad set, and ad without any additional configuration.

**Recommended:** Install the [Meta Pixel Helper](https://chromewebstore.google.com/detail/meta-pixel-helper/fdgfkebogiimcoedlicjlajpkdmockpc) Chrome extension to verify the Pixel is firing correctly before launching campaigns.

---

## Files Added / Modified

### New Files

| File | Purpose |
|------|---------|
| `acceleratedrehabtherapy/templates/base_landing.html` | Stripped-down base template for all landing pages |
| `acceleratedrehabtherapy/templates/includes/_landing_form.html` | Shared lead capture form |
| `acceleratedrehabtherapy/templates/includes/_landing_cta.html` | Reusable mid-page CTA section |
| `acceleratedrehabtherapy/templates/includes/_landing_trust.html` | Reviews slider + trust bullets |
| `acceleratedrehabtherapy/templates/includes/_landing_image_placeholder.html` | Styled placeholder for photos not yet taken |
| `apps/main/templates/main/landing_shockwave_denver.html` | Landing page 1 |
| `apps/main/templates/main/landing_shockwave_greeley.html` | Landing page 2 |
| `apps/main/templates/main/landing_shockwave_plantar_fasciitis.html` | Landing page 3 |
| `apps/main/templates/main/landing_chronic_tendon.html` | Landing page 4 |
| `apps/main/templates/main/landing_non_surgical_denver.html` | Landing page 5 |
| `apps/main/templates/main/landing_thank_you.html` | Shared confirmation page (fires Lead event) |

### Modified Files

| File | Change |
|------|--------|
| `apps/main/models.py` | Added `LandingPageLead` model |
| `apps/main/admin.py` | Registered `LandingPageLead` with full filter/search config |
| `apps/main/views.py` | Added landing views, form submit handler, thank-you view |
| `apps/main/urls.py` | Added 7 new URL patterns |
| `apps/main/migrations/0007_landingpagelead.py` | Migration for the new model |
| `acceleratedrehabtherapy/settings.py` | Added `META_PIXEL_ID`, `LEAD_EMAIL_PRIMARY`, `LEAD_EMAIL_GREELEY`, `LEAD_EMAIL_DENVER` |

---

## Image Placeholders

Each landing page contains styled placeholder blocks where real photography should be placed. The placeholders describe exactly what type of image is needed for each spot. Once photos are available, replace the `{% include 'includes/_landing_image_placeholder.html' %}` tag with a standard `<img>` tag pointing to the uploaded asset.

Recommended image specifications:
- Format: WebP (preferred) or JPG
- Width: 800–1200px
- Aspect ratio: 4:3 or 16:9

---

## Recommended Next Steps

1. **Add `META_PIXEL_ID` to `.env`** — once obtained from Meta Business Manager
2. **Replace image placeholders** — with real clinic and treatment photography
3. **Discuss lead form submission storage** — currently saves to database + sends email; CRM integration can be added later
4. **Launch campaigns** — create separate ad sets per page to track cost-per-lead by condition and location
5. **A/B test headlines** — the headline and CTA button text on each page can be adjusted in the template without touching Python code
6. **Add testimonial videos** — a short embed block can be added to any landing page as video assets become available

---

*Created: 2026-05-12*
