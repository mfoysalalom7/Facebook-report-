# app.py | Python 3.10+ | Flask

from flask import Flask, request, jsonify, render_template
from reporter import run_report

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/report", methods=["POST"])
def report():
    data = request.get_json()
    url = (data or {}).get("url", "").strip()

    if not url:
        return jsonify({"success": False, "message": "URL দাও"}), 400

    if "facebook.com" not in url:
        return jsonify({"success": False, "message": "Facebook URL হতে হবে"}), 400

    result = run_report(url)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
