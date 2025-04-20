import os
from flask import Flask, render_template, request, jsonify, make_response
from scraper.google_scraper import Google
from scraper.utils import create_scraper_input
import requests

app = Flask(__name__)

# === Tor Configuration ===
USE_TOR = os.getenv("USE_TOR", "false").lower() == "true"
TOR_SOCKS_HOST = os.getenv("TOR_SOCKS_HOST", "127.0.0.1")
TOR_SOCKS_PORT = int(os.getenv("TOR_SOCKS_PORT", 9050))
TOR_CONTROL_PORT = int(os.getenv("TOR_CONTROL_PORT", 9051))
TOR_CONTROL_PASSWORD = os.getenv("TOR_CONTROL_PASSWORD", "")

# Try to import stem for Tor control; disable Tor if unavailable
try:
    from stem import Signal
    from stem.control import Controller
    STEM_AVAILABLE = True
except ModuleNotFoundError:
    STEM_AVAILABLE = False
    if USE_TOR:
        print("[WARN] 'stem' library not found; disabling Tor functionality.")
        USE_TOR = False


def create_tor_session():
    """
    Returns a requests.Session routing through Tor's SOCKS5 proxy.
    """
    session = requests.Session()
    proxy = f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}"
    session.proxies.update({
        "http": proxy,
        "https": proxy
    })
    return session


def renew_tor_ip():
    """
    Signals Tor to switch to a new circuit/exit node.
    Only works if 'stem' is available.
    """
    if not STEM_AVAILABLE:
        return
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            controller.authenticate(password=TOR_CONTROL_PASSWORD)
            controller.signal(Signal.NEWNYM)
    except Exception as e:
        print(f"[WARN] Could not renew Tor IP: {e}")


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        job_title = request.form.get("job_title", "")
        location = request.form.get("location", "")

        scraper = Google()
        if USE_TOR:
            renew_tor_ip()
            scraper.session = create_tor_session()

        scraper_input = create_scraper_input(
            search_term=job_title,
            location=location,
            results_wanted=100,
            hours_old=168,
            is_remote=False
        )
        jobs_df = scraper.scrape(scraper_input).to_df()
        return render_template("results.html", jobs=jobs_df)

    return render_template("index.html")


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    data = request.get_json() or {}
    job_title = data.get("job_title", "")
    location = data.get("location", "")

    scraper = Google()
    if USE_TOR:
        renew_tor_ip()
        scraper.session = create_tor_session()

    scraper_input = create_scraper_input(
        search_term=job_title,
        location=location,
        results_wanted=100,
        hours_old=168,
        is_remote=False
    )
    jobs_df = scraper.scrape(scraper_input).to_df()
    response = make_response(jsonify(jobs_df.to_dict(orient="records")))
    # Allow CORS if needed
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


if __name__ == "__main__":
    # Render.com sets the PORT env var
    host = "0.0.0.0"
    port = int(os.getenv("PORT", os.getenv("FLASK_RUN_PORT", 6000)))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)






