# EC2 Booking and Management System

This project is a Django-based web application for booking and managing AWS EC2 instances. It allows users to register for bookings, automatically creates user credentials, provisions EC2 instances, and sends email notifications with instance details.

 ## Features

- User registration for booking EC2 instances
- Automatic creation of user credentials
- Provisioning of EC2 instances with JupyterHub
- Email notifications with booking and instance details
- Scheduled shutdown of EC2 instances

## Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up environment variables in a [.env](http://_vscodecontentref_/41) file:
    ```env
    SECRET_KEY=your_secret_key
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_HOST=your_db_host
    DB_PORT=5432
    TIME_ZONE=your_time_zone
    AWS_ACCESS_KEY_ID=your_aws_access_key_id
    AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
    AWS_DEFAULT_REGION=your_aws_default_region
    ```

5. Run database migrations:
    ```sh
    python manage.py migrate
    ```

6. Start the development server:
    ```sh
    python manage.py runserver
    ```

## Usage

- Access the application at `http://localhost:8000/booking/register/` to register for a booking.
- Admin interface is available at `http://localhost:8000/admin/`.

## Docker

To run the application using Docker:

1. Build and start the containers:
    ```sh
    docker-compose up --build
    ```

2. Access the application at `http://localhost:8001/booking/register/`.

## Testing

To run tests:
```sh
python manage.py test