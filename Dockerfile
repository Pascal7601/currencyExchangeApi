FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libmariadb-dev \
    --no-install-recommends

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python3","manage.py", "runserver", "0.0.0.0:8000"]