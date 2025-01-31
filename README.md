# LearnArc

LearnArc is a peer learning platform for students and teachers, featuring user authentication, classroom management, doubt forum, AI-generated quizzes, and gamified dashboards.

## Features

- User Authentication (Student/Teacher roles)
- Interactive Dashboards
- Classroom Management
- Resource Sharing
- Doubt Forum with Peer Interaction
- AI-Generated Quizzes and Flashcards
- Gamification Elements

## Tech Stack

- Frontend: HTML, CSS
- Backend: Python (Flask)
- Database: PostgreSQL
- AI: Transformers for quiz generation

## Setup Instructions

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file with the following:
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   DATABASE_URL=your_database_url
   ```

4. Initialize the database:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

5. Run the application:
   ```
   flask run
   ```

## Project Structure

```
learnarc/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── templates/
│   └── static/
├── migrations/
├── instance/
├── tests/
├── venv/
├── .env
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```
