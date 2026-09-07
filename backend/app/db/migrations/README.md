# Database migrations
#
# For the MVP the backend uses `Base.metadata.create_all()` on startup
# (see app/db/database.py::init_db) — no manual migration step is needed.
#
# If/when schema changes become risky, TEAM B will introduce Alembic:
#
#   pip install alembic
#   alembic init app/db/migrations       # then point env.py at app.db.base.Base
#   alembic revision --autogenerate -m "..."
#   alembic upgrade head
#
# RULE for the hackathon: schema changes must be announced in the team chat
# BEFORE being pushed — see docs/api/API_CONTRACT.md ("stability rules").
