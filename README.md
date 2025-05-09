# Oracle Database Query Tool

This project provides a simple tool to query Oracle databases using python-oracledb.

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with the following variables:
```
ORACLE_USERNAME=your_username
ORACLE_PASSWORD=your_password
ORACLE_HOST=your_host
ORACLE_PORT=your_port
ORACLE_SERVICE_NAME=your_service_name
```

## Usage

Run the script:
```bash
python oracle_query.py
```

The script will:
1. Connect to the Oracle database using the credentials from .env
2. Execute a query to fetch the latest record from src#1 and src_hist tables
3. Display the results 