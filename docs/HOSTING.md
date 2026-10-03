# Host the complete NHS Django prototype

Prepared for Render using one Python web service and a persistent disk. SQLite and uploaded photos live together under /var/data. This is a small prototype deployment with one service instance. The original team GitHub repository has not been changed. No hosting account, paid resource, or public deployment has been created.

## Deploy when ready

1. Review and extract the ZIP. Use a separate repository you own for the contents of Car-Rental-Service (manage.py and render.yaml at its root). Do not upload db.sqlite3, media, passwords or .env. Publishing this separate repository is a step you perform after reviewing the project.
2. Sign in to Render, choose New Blueprint, and connect that separate repository. Review the proposed Starter service and 1 GB disk costs before creating resources; persistent disks require paid services. See https://render.com/docs/disks and https://render.com/docs/blueprint-spec.
3. Deploy. The build collects static CSS, JavaScript and sample images. Startup runs migrations against the mounted disk. The generated Render hostname is allowed automatically, HTTPS is enforced, and a secret key is generated.
4. In the service Shell run `python manage.py seed_data` once, then `python manage.py createsuperuser`. Never put the admin password in source code. Visit your HTTPS service URL and /admin/.
5. Test registration, login, booking, mock payment, cancellation and a car photo upload. Restart the service and confirm the booking and photo remain. This persistence check requires an actual hosted service and has not been run here.

For a custom domain, set DJANGO_ALLOWED_HOSTS to the exact hostname (comma-separated if multiple) and DJANGO_CSRF_TRUSTED_ORIGINS to https://your-domain.example. Keep the generated secret key stable across deploys. Only run behind a trusted HTTPS proxy that overwrites X-Forwarded-Proto; The Render Blueprint sets WAITRESS_TRUSTED_PROXY=* because Render routes external traffic through its HTTPS proxy. On other hosts, set it to the actual trusted proxy IP; never expose the production server directly to untrusted HTTP traffic.

## Storage and backups

Only files inside /var/data persist on Render. The database is /var/data/db.sqlite3 and uploaded photos are /var/data/media/cars/. Back up both together, using SQLite's backup API or taking the service offline before copying its database. Do not run multiple replicas against this SQLite disk. Seeding is deliberately manual and is not repeated at every restart. Static sample images are shipped with the code. Uploaded images are served through a public route restricted to filenames referenced by cars; image uploads remain restricted to Admin.

## Local Windows use

Normal README setup still works. Production mode is selected with DJANGO_DEBUG=0 and requires DJANGO_SECRET_KEY (at least 50 random characters), exact DJANGO_ALLOWED_HOSTS and persistent DJANGO_DATA_DIR. Use python serve.py behind an HTTPS reverse proxy for production. Use manage.py runserver for the local classroom demo.

## What has been verified

Fresh ZIP installation, migrations, Django checks and automated tests are run locally. Actual Render deployment, billing approval, custom domain and hosted restart persistence require your hosting account. Payments remain simulated; confirmation email uses the console backend.
