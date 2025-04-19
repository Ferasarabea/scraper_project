from flask import Flask, render_template, request, jsonify
from scraper.google_scraper import Google
from scraper.utils import create_scraper_input

app = Flask(__name__)

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
    data = request.get_json()
    job_title = data.get("job_title")
    location = data.get("location")

    if not job_title:
        return jsonify({"error": "job_title is required"}), 400

    scraper = Google()
    scraper_input = create_scraper_input(
        search_term=job_title,
        location=location,
        results_wanted=100,
        hours_old=168,
        is_remote=False
    )
    jobs = scraper.scrape(scraper_input).to_df()
    return jobs.to_json(orient="records")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)




