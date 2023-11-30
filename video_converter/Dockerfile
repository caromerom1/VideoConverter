FROM python:3.12-slim

WORKDIR /video_converter

RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

EXPOSE $API_PORT

CMD ["python", "video_tasks.py"]
