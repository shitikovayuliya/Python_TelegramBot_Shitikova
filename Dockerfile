FROM python:3.11-slim
RUN apt-get update && apt-get install -y libpq-dev gcc
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
