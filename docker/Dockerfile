FROM python:3.9-slim-buster

WORKDIR /bot

COPY requirements.txt .
COPY .env .
COPY db.env .

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install opencv-python

COPY app/ .

CMD ["python", "bot.py"]
