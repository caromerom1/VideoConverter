import os
from flask import Flask

app = Flask(__name__)


@app.route("/api/auth/signup", methods=["POST"])
def signup():
    return "Hello, World!"

@app.route("/api/auth/login", methods=["POST"])
def login():
    return "Hello, World!"


if __name__ == "__main__":
    API_PORT = os.environ.get("API_PORT", 5000)
    app.run(debug=True, port=API_PORT, host="0.0.0.0")
