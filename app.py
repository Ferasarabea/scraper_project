import os
import requests
from flask import Flask, render_template, request, jsonify
from scraper.google_scraper import Google
from scraper.utils import create_scraper_input

app = Flask(__name__)

# === Tor Configuration ===
USE_TOR            = os.getenv("USE_TOR", "false").lower() == "true"
TOR_SOCKS_HOST     = os.getenv("TOR_SOCKS_HOST", "127.0.0.1")
TOR_SOCKS_PORT     = int(os.getenv("TOR_SOCKS_PORT", 9050))
TOR_CONTROL_PORT   = int(os.getenv("TOR_CONTROL_PORT", 9051))
TOR_CONTROL_PW     = os.getenv("TOR_CONTROL_PASSWORD", "")

# Attempt to import stem; disable Tor if missing
try:
    from stem import Signal
    from stem.control import Controller
    STEM_AVAILABLE = True
except ModuleNotFoundError:
    STEM_AVAILABLE = False
    if USE_TOR:
        print("[WARN] stem library not found; disabling Tor.")
        USE_TOR = False


def create_tor_session():
    """Return a requests.Session that tunnels through Tor."""
    sess = requests.Session()
    proxy = f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}"
    sess.proxies.update({"http": proxy, "https": proxy})
    return sess


def renew_tor_ip():
    """Tell Tor to build a new circuit / exit node."""
    if not (USE_TOR and STEM_AVAILABLE):
        return
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as ctrl:
            ctrl.authenticate(password=TOR_CONTROL_PW)
            ctrl.signal(Signal.NEWNYM)
    except Exception as e:
        print(f"[WARN] Could not renew Tor IP: {e}")


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        job_title = request.form.get("job_title", "")
        location  = request.form.get("location", "")

        scraper = Google()
        if USE_TOR:
            renew_tor_ip()
            scraper.session = create_tor_session()

        inp = create_scraper_input(
            search_term   = job_title,
            location      = location,
            results_wanted=100,
            hours_old     = 168,
            is_remote     = False
        )
        jobs_df = scraper.scrape(inp).to_df()
        return render_template("results.html", jobs=jobs_df)

    return render_template("index.html")


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    data      = request.get_json() or {}
    job_title = data.get("job_title", "")
    location  = data.get("location", "")

    scraper = Google()
    if USE_TOR:
        renew_tor_ip()
        scraper.session = create_tor_session()

    inp = create_scraper_input(
        search_term   = job_title,
        location      = location,
        results_wanted=100,
        hours_old     = 168,
        is_remote     = False
    )
    jobs_df = scraper.scrape(inp).to_df()
    return jsonify(jobs_df.to_dict(orient="records"))


if __name__ == "__main__":
    # Render injects PORT; default to 6000 locally
    port  = int(os.getenv("PORT", 6000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)







