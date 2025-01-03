FROM python:3.12-slim
ARG USER_ID=1000
ARG GROUP_ID=1000
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create group and user with dynamic IDs
RUN groupadd -g ${GROUP_ID} django && \
    useradd -u ${USER_ID} -g django -m django

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set permissions for the app directory
RUN mkdir -p /app/static /app/logs && \
    chown -R django:django /app

COPY --chown=django:django requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=django:django . /app/
COPY --chown=django:django entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER django
ENTRYPOINT ["/entrypoint.sh"]