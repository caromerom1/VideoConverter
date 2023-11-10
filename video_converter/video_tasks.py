import os
from celery.exceptions import Ignore
from celery import states
from models import session, Video
from celery_instance import celery
from enums import ConversionStatus
from google.cloud import storage
import tempfile


GCP_BUCKET_NAME = "video-converter-bucket"
client = storage.Client()
bucket = storage.Bucket(client, GCP_BUCKET_NAME)


@celery.task(bind=True)
def convert_video(self, task_details, task_id):
    self.update_state(state=states.STARTED, meta={"status": "Started video conversion"})

    paths = task_details["paths"]
    conversion_extension = task_details["extension"]

    cmd = conversion_command(paths, conversion_extension)

    temp_upload_file = tempfile.NamedTemporaryFile(delete=False).name
    original_file_name = paths["original"]
    paths["original"] = temp_upload_file

    temp_converted_file = tempfile.NamedTemporaryFile(delete=False).name
    converted_file_name = paths["converted"]
    paths["converted"] = temp_converted_file

    try:
        bucket.blob(original_file_name).download_to_filename(temp_upload_file)

        with session() as db:
            video_conversion_task = db.query(Video).filter(Video.id == task_id).first()
            video_conversion_task.status = ConversionStatus.IN_PROGRESS
            video_conversion_task.conversion_task_id = self.request.id
            session.commit()

            if not cmd:
                self.update_state(
                    state=states.FAILURE, meta={"status": "Invalid command"}
                )
                video_conversion_task.status = ConversionStatus.FAILED
                session.commit()
                raise Ignore()

            os.system(cmd)

            bucket.blob(
                f"{converted_file_name}.{conversion_extension}"
            ).upload_from_filename(f"{paths['converted']}.{conversion_extension}")

            original_file_location = original_file_name
            converted_file_location = f"{converted_file_name}.{conversion_extension}"

            self.update_state(
                state=states.SUCCESS,
                meta={"status": f"File saved to {converted_file_location}"},
            )

            video_conversion_task.status = ConversionStatus.SUCCESS
            session.commit()

            return f"Converted {original_file_location} to {converted_file_location}"
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
