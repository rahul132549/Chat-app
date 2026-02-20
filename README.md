chat_app - A minimal real-time chat application

Description: A minimal real-time chat application built with Django, Channels, and WebSockets for instant messaging.

Prerequisites:

Python 3.10 or higher

Redis (Required for real-time broadcasting)

Installation & Setup:

Clone the repository: git clone cd

Create a virtual environment:

Windows: python -m venv venv .\venv\Scripts\Activate.ps1

macOS/Linux: python -m venv venv source venv/bin/activate

Install dependencies: pip install -r requirements.txt

Database setup: python manage.py migrate

(Optional) Create a superuser: python manage.py createsuperuser

Run the development server: python manage.py runserver

Access the app at: http://127.0.0.1:8000/

Notes:

Make sure Redis is running for real-time chat functionality.

Django Channels uses Redis as the backend for WebSockets.
