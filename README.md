# ASEP (Academic Student Engagement Platform)

## Prerequisites
1. Git
2. Python 3.8 or higher
3. pip (Python package installer)

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/amwanshul/ASEP.git
cd ASEP
```

### 2. Set Up Python Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize the Database
```bash
python init_db.py
```

### 5. Run the Application
```bash
python run.py
```

The application should now be running at `http://localhost:5000`

## Common Issues and Solutions

1. If you get an error about Python not being found, make sure Python is installed and added to your system's PATH.
2. If pip is not recognized, install it following the instructions at https://pip.pypa.io/en/stable/installation/
3. Make sure all required ports (default: 5000) are not being used by other applications.

## Environment Variables
Create a `.env` file in the root directory with the following variables:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

## Support
If you encounter any issues, please open an issue on the GitHub repository.
