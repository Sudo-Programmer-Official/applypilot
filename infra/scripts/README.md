# scripts

- `init_postgres.sql`: bootstrap schema for production Postgres/RDS.
- `db_smoke_test.py`: upload a fixture resume through the API and verify Postgres writes land in `parsed_resumes`, `resume_analysis`, and `optimized_resumes`.

Run it with:

```bash
psql "$DATABASE_URL" -f infra/scripts/init_postgres.sql
```

Run the smoke test with:

```bash
PYTHONPATH=. apps/api/.venv/bin/python infra/scripts/db_smoke_test.py
```
