import os
from celery.exceptions import Ignore
from celery import states
from models import session, Video
from celery_instance import celery
from enums import ConversionStatus


@celery.task(bind=True)
def convert_video(
    self, task_details, task_id
):
    self.update_state(state=states.STARTED, meta={"status": "Started video conversion"})

    paths = task_details["paths"]
    conversion_extension = task_details["extension"]


    cmd = conversion_command(paths, conversion_extension)

    with session() as db:
        video_conversion_task = (
            db.query(Video).filter(Video.id == task_id).first()
        )
        video_conversion_task.status = ConversionStatus.IN_PROGRESS
        video_conversion_task.conversion_task_id = self.request.id
        session.commit()

        if not cmd:
            self.update_state(state=states.FAILURE, meta={"status": "Invalid command"})
            video_conversion_task.status = ConversionStatus.FAILED
            session.commit()
            raise Ignore()

        os.system(cmd)

        original_file_location = paths["original"]
        converted_file_location = f"{paths['converted']}.{conversion_extension}"

        self.update_state(
            state=states.SUCCESS,
            meta={"status": f"File saved to {converted_file_location}"},
        )

        video_conversion_task.status = ConversionStatus.SUCCESS
        session.commit()

        return f"Converted {original_file_location} to {converted_file_location}"


def conversion_command(paths, conversion_extension):
    conversion_commands = {
        "mp4": f"ffmpeg -i {paths['original']} {paths['converted']}.mp4",
        "webm": f"ffmpeg -i {paths['original']} {paths['converted']}.webm",
        "avi": f"ffmpeg -i {paths['original']} {paths['converted']}.avi",
        "wmv": f"ffmpeg -i {paths['original']} {paths['converted']}.wmv",
        "mpeg": f"ffmpeg -i {paths['original']} {paths['converted']}.mpeg",
    }

    return conversion_commands.get(conversion_extension, None)
