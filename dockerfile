FROM python:3.12-slim

# Create a user with a specific UID and GID that matches typical WSL2 user
ARG USER_ID=1000
ARG GROUP_ID=1000

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create group and user with specific UID/GID
RUN groupadd -g ${GROUP_ID} django && \
    useradd -u ${USER_ID} -g django -m django

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt


# Copy project files
COPY . /app/

# Create log directory and ensure proper permissions
# RUN mkdir -p /app/logs && \
#     touch /app/logs/ec2_creation.log && \
#     chown -R ${USER_ID}:${GROUP_ID} /app

# RUN python manage.py migrate

# Switch to the created user
USER django



# Command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]