FROM python:3.10-slim-buster

RUN mkdir -p /app
RUN groupadd app && useradd -g app app

WORKDIR /app

COPY src/ .
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["python3", "app.py"]