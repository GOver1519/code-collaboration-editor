# ============================================================
# IMPORT POSTGRESQL LIBRARY
# ============================================================

# psycopg2 is a PostgreSQL adapter for Python
# It allows Python applications to communicate
# with PostgreSQL databases
import psycopg2


# ============================================================
# DATABASE CONNECTION
# ============================================================

# psycopg2.connect() creates connection between:
# Python application ↔ PostgreSQL database
conn = psycopg2.connect(

    # Database server location
    # localhost means database is running on same computer
    host="localhost",

    # Database name inside PostgreSQL
    database="collab_editor",

    # PostgreSQL username
    user="postgres",

    # PostgreSQL password
    password="Aa123456!12"
)


# ============================================================
# DATABASE CURSOR
# ============================================================

# cursor is used to execute SQL queries like:
# - SELECT
# - INSERT
# - UPDATE
# - DELETE
#
# Think of cursor as a communication tool
# between Python and PostgreSQL
cursor = conn.cursor()