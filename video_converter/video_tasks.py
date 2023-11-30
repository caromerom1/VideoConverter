import base64
import os

from flask import Flask, jsonify, request

from models import session, Video
from enums import ConversionStatus
from google.cloud import storage
import tempfile
import json

app = Flask(__name__)

GCP_BUCKET_NAME = "video-converter-bucket"
client = storage.Client()
bucket = storage.Bucket(client, GCP_BUCKET_NAME)


def convert_video(video_data):
    conversion_extension = video_data["extension"]
    task_id = video_data["task_id"]

    paths = {
        "original": video_data["original_path"],
        "converted": video_data["converted_path"],
    }

    temp_upload_file = tempfile.NamedTemporaryFile(delete=False).name
    original_file_name = paths["original"]
    paths["original"] = temp_upload_file

    temp_converted_file = tempfile.NamedTemporaryFile(delete=False).name
    converted_file_name = paths["converted"]
    paths["converted"] = temp_converted_file

    cmd = conversion_command(paths, conversion_extension)

    try:
        bucket.blob(original_file_name).download_to_filename(temp_upload_file)

        with session() as db:
            video_conversion_task = db.query(Video).filter(Video.id == task_id).first()
            video_conversion_task.status = ConversionStatus.IN_PROGRESS
            session.commit()

            if not cmd:
                video_conversion_task.status = ConversionStatus.FAILED
                session.commit()
                return jsonify({"status": "ERROR", "message": "Conversion failed"}), 400

            convertion_status = os.system(cmd)

            if convertion_status != 0:
                video_conversion_task.status = ConversionStatus.FAILED
                session.commit()
                return jsonify({"status": "ERROR", "message": "Conversion failed"}), 500

            bucket.blob(
                f"{converted_file_name}.{conversion_extension}"
            ).upload_from_filename(f"{paths['converted']}.{conversion_extension}")

            original_file_location = original_file_name
            converted_file_location = f"{converted_file_name}.{conversion_extension}"

            video_conversion_task.status = ConversionStatus.SUCCESS
            session.commit()

            app.logger.info(
                f"Converted {original_file_location} to {converted_file_location}"
            )
            return (
                jsonify(
                    {
                        "status": "SUCCESS",
                        "message": f"Converted {original_file_location} to {converted_file_location}",
                    }
                ),
                200,
            )

    finally:
        os.remove(temp_upload_file)
        os.remove(temp_converted_file)


def conversion_command(paths, conversion_extension):
    conversion_commands = {
        "mp4": f"ffmpeg -i {paths['original']} {paths['converted']}.mp4",
        "webm": f"ffmpeg -i {paths['original']} {paths['converted']}.webm",
        "avi": f"ffmpeg -i {paths['original']} {paths['converted']}.avi",
        "wmv": f"ffmpeg -i {paths['original']} {paths['converted']}.wmv",
        "mpeg": f"ffmpeg -i {paths['original']} {paths['converted']}.mpeg",
    }

    return conversion_commands.get(conversion_extension, None)


@app.route("/convert-video", methods=["POST"])
def pubsub_push():
    envelope = request.get_json()

    if not envelope:
        msg = "no Pub/Sub message received"
        app.logger.error(f"error: {msg}")
        return f"Bad Request: {msg}", 400

    if not isinstance(envelope, dict) or "message" not in envelope:
        msg = "invalid Pub/Sub message format"
        app.logger.error(f"error: {msg}")
        return f"Bad Request: {msg}", 400

    pubsub_message = envelope["message"]

    if not isinstance(pubsub_message, dict) and not "data" in pubsub_message:
        msg = "invalid Pub/Sub message format"
        app.logger.error(f"error: {msg}")
        return ("", 204)

    video_data = json.loads(base64.b64decode(pubsub_message["data"]).decode("utf-8"))
    app.logger.info(
        f"Received video conversion task {video_data['task_id']} for {video_data['original_path']}."
    )

    try:
        convert_video(video_data)
    except Exception as e:
        app.logger.error(f"Error converting video: {e}")
        return ("", 500)


@app.route("/healthcheck", methods=["GET"])
def signup():
    return jsonify({"message": "OK"}), 200


if __name__ == "__main__":
    CONVERTER_PORT = os.environ.get("CONVERTER_PORT", 5000)
    app.run(debug=True, port=CONVERTER_PORT, host="0.0.0.0")
