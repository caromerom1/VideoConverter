FROM python:3.12-slim

WORKDIR /video_converter

RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "video_tasks.py"]
