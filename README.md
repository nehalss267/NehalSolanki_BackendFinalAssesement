# Backend Project

## Setup Instructions

### Prerequisites
- Python 3.11+
- pip
- Virtual environment

### Installation

1. Clone the repository
`ash
git clone <repository-url>
cd backendProject
`

2. Create and activate virtual environment
`ash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
`

3. Install dependencies
`ash
pip install -r requirements.txt
`

4. Set up environment variables
`ash
cp .env.example .env
# Update .env with your configuration
`

5. Apply database migrations
`ash
python manage.py migrate
`

6. Create a superuser (optional)
`ash
python manage.py createsuperuser
`

7. Run the development server
`ash
python manage.py runserver
`

The API will be available at http://localhost:8000/

## API Documentation

Interactive API documentation is available via Swagger UI and ReDoc:

- **Swagger UI**: [http://localhost:8000/swagger/](http://localhost:8000/swagger/)
- **ReDoc**: [http://localhost:8000/redoc/](http://localhost:8000/redoc/)
- **API Root**: [http://localhost:8000/api/](http://localhost:8000/api/)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/health/ | GET | Health check endpoint |
| /api/health/ping/ | GET | Ping endpoint |
| /api/users/ | GET | List all users |
| /api/users/{id}/ | GET | Retrieve a specific user |

## Features

- Django 5.2+ REST Framework
- Interactive API documentation with Swagger/OpenAPI
- Environment-based configuration
- RESTful API structure
- Database migrations

## Testing

`ash
python manage.py test
`

## Admin Panel

Access the Django admin at [http://localhost:8000/admin/](http://localhost:8000/admin/)

## License

This project is for educational purposes.
