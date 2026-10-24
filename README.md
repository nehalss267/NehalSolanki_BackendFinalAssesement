# Backend Project

## Setup Instructions

### Prerequisites
- Python 3.11+
- pip

### Installation

1. Clone the repository
`ash
git clone <repository-url>
cd backendProject
`

2. Create virtual environment
`ash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
`

3. Install dependencies
`ash
pip install -r requirements.txt
`

4. Environment Variables
`ash
cp .env.example .env
# Edit .env with your configuration
`

5. Run migrations
`ash
python manage.py migrate
`

6. Create superuser
`ash
python manage.py createsuperuser
`

7. Run development server
`ash
python manage.py runserver
`

## API Documentation
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

## Usage
Access the API endpoints at http://localhost:8000/api/
