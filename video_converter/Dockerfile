FROM python:3.12-slim

WORKDIR /video_converter

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

CMD ["celery", "-A", "video_tasks", "worker", "--loglevel=info"]
