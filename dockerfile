FROM python:3.12-slim

ARG USER_ID=1000
ARG GROUP_ID=1000

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create group and user with dynamic IDs
RUN groupadd -g ${GROUP_ID} django && \
    useradd -u ${USER_ID} -g django -m django

WORKDIR /app

# Install system dependencies including Redis client
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    supervisor \
    redis-tools \
    htop \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set permissions for the app directory
RUN mkdir -p /app/static /app/logs && \
    chown -R django:django /app

# Copy and install requirements first for better caching
COPY --chown=django:django requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY --chown=django:django . /app/
COPY --chown=django:django entrypoint.sh /entrypoint.sh
COPY --chown=django:django supervisord.conf /etc/supervisord.conf
RUN chmod +x /entrypoint.sh

# Add health check for the web service
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

USER django
ENTRYPOINT ["/entrypoint.sh"]