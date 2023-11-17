from datetime import timedelta

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

import json
import os
from enums.ConversionStatus import ConversionStatus
from models import db, Video, VideoSchema
from google.cloud import pubsub_v1, storage
from google.auth.transport import requests
from google.auth import compute_engine

video_bp = Blueprint("video", __name__)

GCP_BUCKET_NAME = "video-converter-bucket"
client = storage.Client()
bucket = storage.Bucket(client, GCP_BUCKET_NAME)

project_id = os.environ.get("GCP_PROJECT_ID", "")
topic_name = os.environ.get("GCP_TOPIC_ID", "")
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)

@video_bp.route("/", methods=["GET"])
@jwt_required()
def get_all_videos():
    request_data = request.json
    user_id = get_jwt_identity()
    order = request_data.get("order", None)
    max = request_data.get("max", None)
    videos_tasks = Video().query.filter(Video.user_id == user_id)

    if order:
        order_criteria = Video.id.desc() if order == "1" else Video.id.asc()

        videos_tasks = videos_tasks.order_by(order_criteria)

    if max:
        videos_tasks = videos_tasks.limit(max)

    query_result = videos_tasks.all()

    return jsonify(VideoSchema(many=True).dump(query_result)), 200


@video_bp.route("/<task_id>", methods=["GET"])
@jwt_required()
def get_video(task_id):
    if not task_id:
        return jsonify({"message": "No task_id provided"}), 400

    user_id = get_jwt_identity()

    video_task = (
        Video().query.filter(Video.user_id == user_id, Video.id == task_id).first()
    )

    if not video_task:
        return jsonify({"message": "No video found"}), 404

    video_task_data = VideoSchema().dump(video_task)

    auth_request = requests.Request()
    signing_credentials = compute_engine.IDTokenCredentials(auth_request, "")

    original_url = bucket.blob(video_task.original_path).generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=5),
        method="GET",
        credentials=signing_credentials,
    )

    converted_url = bucket.blob(video_task.converted_path).generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=5),
        method="GET",
        credentials=signing_credentials,
    )

    video_task_data["original"] = original_url
    video_task_data["converted"] = converted_url

    return jsonify(video_task_data), 200


@video_bp.route("/", methods=["POST"])
@jwt_required()
def convert_video():
    file = request.files["video"]

    if not request.files.get("video") or not file.filename:
        return jsonify({"msg": "No video uploaded"}), 400

    conversion_extension = request.form.get("conversion_extension")

    if not conversion_extension:
        return jsonify({"msg": "No conversion extension provided"}), 400

    if conversion_extension[0] == ".":
        conversion_extension = conversion_extension[1:]

    allowed_extensions = ["mp4", "webm", "avi", "wmv", "mpeg"]

    if conversion_extension not in allowed_extensions:
        return (
            jsonify(
                {
                    "msg": f"Conversion extension not allowed ({conversion_extension}). Allowed extensions are: {', '.join(allowed_extensions)}"
                }
            ),
            400,
        )

    user_id = get_jwt_identity()

    user_uploaded_folder = f"{current_app.config['ORIGINALS_FOLDER']}/{user_id}"
    user_converted_folder = f"{current_app.config['CONVERTED_FOLDER']}/{user_id}"

    secured_filename = secure_filename(file.filename)

    base_filename = secured_filename.split(".")[0]

    original_file_location = f"{user_uploaded_folder}/{secured_filename}"

    blob = bucket.blob(original_file_location)
    blob.upload_from_file(file)

    converted_file_location = f"{user_converted_folder}/{base_filename}"

    video_task = Video(
        user_id=user_id,
        original_path=original_file_location,
        converted_path=f"{converted_file_location}.{conversion_extension}",
        conversion_extension=conversion_extension,
    )

    db.session.add(video_task)
    db.session.commit()

    try:
        video_data = json.dumps(
            {
                "task_id": video_task.id,
                "converted_path": converted_file_location,
                "original_path": original_file_location,
                "extension": conversion_extension,
            }
        ).encode("utf-8")
        future = publisher.publish(topic_path, data=video_data)
        future.result()

        return (
            jsonify(
                {
                    "message": "Converting video...",
                    "task_id": video_task.id,
                }
            ),
            200,
        )

    except Exception as e:
        video_task.status = ConversionStatus.FAILED
        db.session.commit()
        return jsonify({"message": str(e)}), 500


@video_bp.route("/<task_id>", methods=["DELETE"])
@jwt_required()
def delete_video(task_id):
    if not task_id:
        return jsonify({"message": "No task_id provided"}), 400

    user_id = get_jwt_identity()

    video_task = (
        Video().query.filter(Video.user_id == user_id, Video.id == task_id).first()
    )

    if not video_task:
        return jsonify({"message": "No video found"}), 404

    if video_task.status != ConversionStatus.SUCCESS:
        return jsonify({"message": "Video not converted yet"}), 400

    bucket.delete_blob(video_task.original_path)
    bucket.delete_blob(video_task.converted_path)

    db.session.delete(video_task)
    db.session.commit()

    return jsonify({"message": "Video deleted succesfully"}), 200
