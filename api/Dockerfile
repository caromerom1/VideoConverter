FROM python:3.12-slim

WORKDIR /api

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

RUN mkdir -p /converter/media/uploaded
RUN mkdir -p /converter/media/converted

EXPOSE $API_PORT

CMD ["python", "app.py"]
