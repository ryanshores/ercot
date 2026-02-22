#!/bin/bash
set -e

echo "Checking database migration state..."

# Check if alembic_version table exists (i.e., is this an existing deployment?)
ALEMBIC_EXISTS=$(python -c "
from sqlalchemy import inspect, create_engine
from src.db.database import SQLALCHEMY_DATABASE_URL
import os
engine = create_engine(SQLALCHEMY_DATABASE_URL)
inspector = inspect(engine)
print('yes' if 'alembic_version' in inspector.get_table_names() else 'no')
")

echo "Alembic version table exists: $ALEMBIC_EXISTS"

if [ "$ALEMBIC_EXISTS" = "no" ]; then
    # Check if our tables already exist (existing deployment without Alembic)
    TABLES_EXIST=$(python -c "
from sqlalchemy import inspect, create_engine
from src.db.database import SQLALCHEMY_DATABASE_URL
import os
engine = create_engine(SQLALCHEMY_DATABASE_URL)
inspector = inspect(engine)
# Use a table you know exists in your schema
print('yes' if 'gen_instant' in inspector.get_table_names() else 'no')
")

    if [ "$TABLES_EXIST" = "yes" ]; then
        echo "Existing deployment detected — stamping with current head..."
        alembic stamp head
    else
        echo "Fresh deployment detected — migrations will build schema..."
    fi
fi

echo "Running migrations..."
alembic upgrade head

echo "Starting application..."
exec python -m src.main