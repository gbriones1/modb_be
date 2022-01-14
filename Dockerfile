FROM python:3.8-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONFAULTHANDLER=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100
ENV POETRY_VERSION=1.1.12

COPY . .

RUN pip install "poetry==$POETRY_VERSION" && \
    poetry export -f requirements.txt --output requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# RUN pip install "poetry==$POETRY_VERSION" && \
#     poetry config virtualenvs.create false  && \
#     poetry install --no-dev --no-interaction --no-ansi

CMD [ "uvicorn", "main.server:app", "--host", "0.0.0.0" ]
