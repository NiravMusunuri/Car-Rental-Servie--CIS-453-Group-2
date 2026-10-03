"""Production WSGI server (Windows and Linux)."""
import os
from waitress import serve
from carrental.wsgi import application
if __name__ == "__main__":
    serve(application, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), threads=4, trusted_proxy=os.environ.get("WAITRESS_TRUSTED_PROXY"), trusted_proxy_headers={"x-forwarded-proto"} if os.environ.get("WAITRESS_TRUSTED_PROXY") else set())
