import hashlib

from flask import Blueprint
from flask import jsonify, request
from flask_jwt_extended import create_access_token

from models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    user = User().query.filter(User.email == request.json["email"]).first()

    password = request.json["password"]

    if user is not None:
        return jsonify({"message": "User already exists"}), 400

    encrypted_password = hashlib.md5(password.encode("utf-8")).hexdigest()
    new_user = User(
        username=request.json["username"],
        email=request.json["email"],
        password=encrypted_password,
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    user = User().query.filter(User.email == request.json["email"]).first()

    encrypted_password = hashlib.md5(
        request.json["password"].encode("utf-8")
    ).hexdigest()

    if user is None or encrypted_password != user.password:
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.id)

    return (
        jsonify(
            {
                "message": "User logged in successfully",
                "token": access_token,
                "id": user.id,
            }
        ),
        200,
    )
