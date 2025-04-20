from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from scraper.google_scraper import Google
from scraper.utils import create_scraper_input

app = Flask(__name__)
CORS(app)  # 🚨 This enables CORS for all routes

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        job_title = request.form["job_title"]
        location = request.form["location"]

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

@app.route("/api/google-jobs", methods=["POST"])
def google_jobs_api():
    data = request.json
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
    app.run(host="0.0.0.0", port=6000, debug=True)





