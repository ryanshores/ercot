# ERCOT Data Visualization

Pulls energy mix from ERCOT every 30 minutes and serves daily and time-series dashboards.

The import uses ERCOT’s net `Power Storage` value and excludes the redundant charging/discharging breakdown fields. Pie chart files and the image gallery are no longer generated or served. Existing image files can remain archived in the old Docker volume.

The live feed contains a rolling three-day window. Restarting the importer recovers that window, but older missing data requires a separate historical backfill.

## Running

```bash
python main.py
```

## Production Readiness

This setup is designed to be production-ready with the following features:

- **Database Migrations (Alembic)**: Database schema is managed via Alembic. The application is configured to run `alembic upgrade head` on startup in the Docker environment via `entrypoint.sh`.
- **Environment Configuration**: Key settings are controllable via environment variables:
  - `SQLALCHEMY_DATABASE_URL`: Connection string for the database (e.g., `postgresql://user:pass@host/db`).
  - `APP_MODE`: Set to `prod` for production or `dev` for development.
- **Service Isolation**: In production mode (`APP_MODE=prod`), the background ERCOT data fetching and the FastAPI web server run in separate threads, ensuring the UI remains responsive.

## Database Migrations (Alembic)

This project uses Alembic to manage database schema changes.

### Initializing Database
Handled by entrypoint script. 

### Creating New Migrations
After modifying models in `src/models/`, generate a new migration script:

```bash
PYTHONPATH=. alembic revision --autogenerate -m "Describe your changes"
```

Then apply it (or run with entrypoint):

```bash
PYTHONPATH=. alembic upgrade head
```

```bash
sh entrypoint.sh
```

## Deploying

```bash
docker-compose up -d
```


## Portainer production deployments

See [Portainer deployment setup](docs/portainer-deployments.md) for the main-only workflow, production stack, access hardening, and activation steps. Webhook delivery stays disabled until setup is complete. Staging and PR previews are deferred.
