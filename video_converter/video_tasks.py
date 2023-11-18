import os
from models import session, Video
from enums import ConversionStatus
from google.cloud import pubsub_v1, storage
from google.cloud.pubsub_v1.types import FlowControl
import tempfile
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

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
                return {"status": "ERROR", "message": "Conversion failed"}

            convertion_status = os.system(cmd)

            if convertion_status != 0:
                video_conversion_task.status = ConversionStatus.FAILED
                session.commit()
                return {"status": "ERROR", "message": "Conversion failed"}

            bucket.blob(
                f"{converted_file_name}.{conversion_extension}"
            ).upload_from_filename(f"{paths['converted']}.{conversion_extension}")

            original_file_location = original_file_name
            converted_file_location = f"{converted_file_name}.{conversion_extension}"

            video_conversion_task.status = ConversionStatus.SUCCESS
            session.commit()

            logger.info(f"Converted {original_file_location} to {converted_file_location}")
            return {
                "status": "SUCCESS",
                "message": f"Converted {original_file_location} to {converted_file_location}",
            }

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


def subscriber_callback(message):
    video_data = json.loads(message.data.decode("utf-8"))

    task_result = convert_video(video_data)

    if task_result.get("status") == "SUCCESS":
        message.ack()
    else:
        message.nack()

    logger.info(task_result)


def main():
    project_id = os.environ.get("GCP_PROJECT_ID")
    subscription_id = os.environ.get("GCP_SUBSCRIPTION_ID")

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    logger.info(f"Listening for messages on {subscription_path}\n")

    flow_control = FlowControl(max_messages=1)

    future = subscriber.subscribe(subscription_path, callback=subscriber_callback, flow_control=flow_control)

    try:
        future.result(timeout=30)
    except KeyboardInterrupt:
        future.cancel()  # Trigger the shutdown.
        future.result()  # Block until the shutdown is complete.


if __name__ == "__main__":
    main()
