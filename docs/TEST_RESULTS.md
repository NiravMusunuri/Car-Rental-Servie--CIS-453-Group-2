# Validation evidence

Validation performed on the local Windows environment using Django 5.2.17.

- Fresh migration from an empty SQLite database: passed (including original 0001/0002 and new 0003).
- Django system check: no issues.
- 20 automated tests: passed; initial complete run took 11.165 seconds.
- Separate file-backed SQLite concurrency check: passed. Two simultaneous reservations for the same car/dates produced exactly one booking and one conflict rejection.
- Sample data command: created six cars across three categories; repeat run leaves the fleet unchanged.
- Extracted deliverable ZIP into a fresh temporary folder: migrations, sample data, system check, and all 20 tests passed again (11.777 seconds).
- Started the actual Django development server from the extracted ZIP: catalog, car details, registration, login, and static CSS returned HTTP 200.

Tests cover account validation/hashing, authentication/logout, ownership privacy, date boundaries, blocked cars, overlap/adjacency, authoritative pricing, filters and invalid query handling, mock payments and consent, confirmation email, cancellation/refunds, modification conflicts/rate retention, pickup-day restrictions, profile/details, admin access/validation, CSRF, and sample-data idempotency.

Run the commands in README.md to reproduce. Test databases are separate from db.sqlite3.
The concurrency script creates and removes its own temporary database.

For class demo/screenshots, follow README's walkthrough and capture the catalog, registration/login, booking dates, checkout/confirmation, My bookings, and Admin pages. No screenshots or personal reflection/team contribution claims are fabricated.

UI refresh: all 20 automated Django tests passed again from a freshly extracted ZIP. Edge browser checks passed at widths 320, 390, 768, 1280 and 1820 px without horizontal overflow. Verified six loaded catalog images, detail image, login/register layouts, theme persistence after reload, and no JavaScript page errors. Light/dark desktop and mobile screenshots were visually reviewed.

Hosting preparation: Django check --deploy passed without warnings; collectstatic succeeded; production mode HTTPS redirect, accepted proxy HTTPS header, unknown host rejection and catalog rendering verified locally. Media endpoint checks cover uploaded photos and rejection of missing/non-car paths. No external deployment performed.
