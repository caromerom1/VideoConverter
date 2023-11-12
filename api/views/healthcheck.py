from flask import Blueprint, jsonify

healthcheck_bp = Blueprint("healthcheck", __name__)


@healthcheck_bp.route("/healthcheck", methods=["GET"])
def signup():
    return jsonify({"message": "OK"}), 200
