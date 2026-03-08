# scripts

- `init_postgres.sql`: bootstrap schema for production Postgres/RDS.

Run it with:

```bash
psql "$DATABASE_URL" -f infra/scripts/init_postgres.sql
```
