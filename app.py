from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from scraper.google_scraper import Google
from scraper.utils import create_scraper_input

app = Flask(__name__)
# Enable CORS for all routes (adjust origins as needed)
CORS(app)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        job_title = request.form.get("job_title")
        location = request.form.get("location")

        scraper = Google()
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
    data = request.get_json(force=True)
    job_title = data.get("job_title")
    location = data.get("location")

    scraper = Google()
    scraper_input = create_scraper_input(
        search_term=job_title,
        location=location,
        results_wanted=100,
        hours_old=168,
        is_remote=False
    )
    jobs_df = scraper.scrape(scraper_input).to_df()
    return jsonify(jobs_df.to_dict(orient="records"))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    # Bind to all interfaces so ngrok or other services can reach the app
    app.run(host="0.0.0.0", port=port, debug=True)
