# ============================================================
# IMPORT LIBRARIES
# ============================================================

import os
import psycopg2

# ============================================================
# GET DATABASE URL FROM RENDER ENVIRONMENT VARIABLES
# ============================================================

# Render automatically provides DATABASE_URL when you add it
DATABASE_URL = os.environ.get("DATABASE_URL")

# Safety check (helps debugging on Render)
if not DATABASE_URL:
    raise Exception("DATABASE_URL not found in environment variables")

# ============================================================
# CONNECT TO POSTGRESQL (RENDER CLOUD DB)
# ============================================================

conn = psycopg2.connect(DATABASE_URL)

# Cursor used to execute SQL queries
cursor = conn.cursor()
