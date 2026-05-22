# Headphone Online Store – SQL Database & Management Interface

This repository contains a university database project that models an online store for headphones. The project consists of an Oracle SQL database structure and a simple web interface built with Python and Flask to manage the data.

The complete documentation in **romanian** for this project can be found in the **`docs/`** folder:
* **[Database Architecture](docs/Documentatie.pdf)**: Explains the table schemas, constraints, and 3NF normalization.
* **[Database Interaction Guide](docs/Interactiune-Baza-De-Date.pdf)**: Contains screenshots of the interface and examples of the advanced SQL queries.


## Project Features

* **3NF Database Design**: The relational schema consists of 7 entities structured according to Third Normal Form rules.
* **Basic Web Operations**: A Python/Flask interface that allows viewing, editing, adding and deleting records from the database tables.

## Technologies Used

* **Database Backend**: Oracle Database (SQL)
* **Web Framework**: Python 3 + Flask
* **Database Tools**: Oracle SQL Developer / SQL*Plus (for script execution and testing)
* **Frontend UI**: HTML, CSS, Bootstrap 

## How to Run the Project

### 1. Initialize the Database
Run the SQL script in your local Oracle Database instance (e.g., via SQL Developer) to create the tables and insert the sample data:
```sql
@script.sql
```

### 2. Install requirements
Make sure you have Python installed, then install Flask and the Oracle database driver:
```
pip install flask oracledb
```

### 3. Update database configuration
Open main.py and modify the connection configuration with your local database username and password:
```
DB_CONFIG = {
    "user": "your_username",
    "password": "your_password",
    "dsn": "localhost:1521/xe"
}
```

### 4. Start the application
Run the main script from your terminal or command prompt:
```
python main.py
```
Open your web browser and go to http://127.0.0.1:5000/.
