# Site Review Recommendations

Findings from a full review of templates, backend code, static assets, and CI/CD configuration. Items are grouped by category and ordered within each group by priority.

---

## Content & Data Consistency

### High Priority

**1. Standardize the Greeley office address**
- Footer shows: `1705 61st Ave Unit M`
- `templates/includes/_structured_data.html` shows: `1705 61st Ave Unit C`
- Pick one and update both locations.

**2. Fix phone number in service page schema**
- The chiropractic and physical therapy page schemas reference `+19703517465`
- The correct number is `970-324-1750` (`+19703241750`)
- Update the schema blocks in `apps/main/templates/main/chiropractor.html` and `physical_therapy.html`

**3. Update social media URLs in structured data**
- `templates/includes/_structured_data.html` still contains placeholder URLs:
  - `https://www.facebook.com/yourpage`
  - `https://www.instagram.com/yourprofile`
- Replace with the actual URLs already used in the footer:
  - Facebook Greeley: `https://www.facebook.com/AcceleratedRehab2020/`
  - Facebook Denver: `https://www.facebook.com/profile.php?id=61582632433440`
  - Instagram: `https://www.instagram.com/greeleyrehab/`

### Medium Priority

**4. Add a re-open date for the UNC Campus location**
- Footer and `_locations_map.html` show "Closed for the Summer" with no context for when it reopens
- Consider adding an estimated re-open date or removing the badge once open

**5. Fix "Learn More" placeholder links in resources page**
- Several buttons in `apps/main/templates/main/resources.html` link to `#`
- Replace with actual internal page URLs or remove the buttons

**6. Verify blog article image paths**
- `templates/includes/_blog_articles.html` references four images that need to exist in `static/img/`:
  - `Chiro assessing neck_small.png`
  - `Man with neck pain_small.png`
  - `Mountain top_small.png`
  - `healthy spine_small.png`

**7. Complete the partners section**
- `templates/includes/_partners.html` shows only one partner with a comment noting more should be added

---

## Security

### High Priority

**8. Remove the hardcoded SECRET_KEY fallback**
- `settings.py` falls back to a hardcoded insecure key if `SECRET_KEY` is missing from `.env`
- Remove the fallback value; make the env var required so a misconfigured deployment fails loudly

**9. Change DEBUG default to False**
- `settings.py`: `DEBUG = os.getenv('DEBUG', 'True') == 'True'`
- The default should be `'False'` so a missing env var doesn't accidentally expose debug error pages in production

**10. Remove or gate the debug review endpoint**
- `/api/test-google-reviews/` is a live production route used only for development testing
- Either delete it or wrap it in `if settings.DEBUG:` in `apps/main/urls.py`

### Medium Priority

**11. Add HTTPS security headers to settings**
- The following are not configured for production:
  ```python
  SECURE_SSL_REDIRECT = True
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  SECURE_HSTS_SECONDS = 31536000
  SECURE_HSTS_INCLUDE_SUBDOMAINS = True
  ```

**12. Add contact form validation and rate limiting**
- `views.py` contact handler checks only that fields are non-empty; no email format validation
- No rate limiting or CAPTCHA — the form can be flooded
- Consider `django-ratelimit` and Django's `EmailField` validators

**13. Remove development hosts from ALLOWED_HOSTS**
- `settings.py` includes `'localhost'`, `'127.0.0.1'`, and `'0.0.0.0'` alongside production domains
- These should be in a dev-only settings override, not the shared settings file

---

## Code Quality

**14. Fix duplicate home() function definition**
- `apps/main/views.py` defines `home()` twice; the second silently overwrites the first
- Delete the redundant definition

**15. Remove print statements and module-level logging.basicConfig()**
- `views.py` has `print()` calls and `logging.basicConfig()` at module scope (runs on every import)
- Remove the prints; logging is already configured in `settings.py`

**16. Fix Windows-specific NPM path**
- `settings.py`: `NPM_BIN_PATH = r"C:\Program Files\nodejs\npm.cmd"`
- This breaks on the Linux production server; use the system PATH instead (remove the setting or use `os.getenv`)

**17. Convert Spanish info page to a template**
- `views.py` `es_info()` renders a large block of HTML directly from Python
- Move this to `apps/main/templates/main/es_info.html` for maintainability

**18. Replace bare exception handlers**
- Multiple `except Exception:` blocks in `views.py` suppress all errors including `SystemExit`
- Catch specific exceptions (`requests.RequestException`, `FileNotFoundError`, etc.)

---

## Performance

**19. Optimize hero images**
- Large PNG hero images (2–3 MB each) are in `static/img/`
- Smaller variants exist alongside them — confirm templates are using the small versions where appropriate
- Consider converting to WebP format for additional compression

**20. Break up the resources page**
- `apps/main/templates/main/resources.html` loads four full long-form blog articles on one page
- Consider tabbed sections, accordions, or separate article pages to reduce initial load

---

## Testing & Infrastructure

**21. Add test coverage**
- `apps/main/tests.py` is empty
- Priority areas: contact form validation, reviews API response handling, view status codes

**22. Configure PostgreSQL for all environments**
- `settings.py` configures SQLite; the README states PostgreSQL is intended for production
- Align settings with a `DATABASE_URL` env var (already in `.env.example`) using `dj-database-url`

---
## Landing Pages
- All landing pages are well-structured and follow a consistent pattern
- Consider adding more specific meta descriptions and Open Graph tags for better social sharing
- Ensure all images have proper alt text for accessibility
- Test mobile responsiveness thoroughly, especially the sticky call bar
- Suggestions: adding more detailed events later, such as Contact, Schedule, or Call button click, but your current PageView + Lead setup is the correct simple starting point.

*Review conducted: 2026-05-11*
