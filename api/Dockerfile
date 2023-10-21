FROM python:3.12-slim

WORKDIR /api

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

RUN mkdir -p /converter/media/uploaded
RUN mkdir -p /converter/media/converted

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
