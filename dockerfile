FROM python:3.12-slim

ARG USER_ID=1000 
ARG GROUP_ID=1000

ENV PYTHONDONTWRITEBYTECODE 1 
ENV PYTHONUNBUFFERED 1

RUN groupadd -g ${GROUP_ID} django && \
    useradd -u ${USER_ID} -g django -m django

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Add entrypoint script to handle migrations
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to the created user
USER django

# Use the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]