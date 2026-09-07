"""
Imports every ORM model so `Base.metadata` knows the full schema.

Used by `init_db()` and (later) by Alembic `env.py`.
"""

from app.db.database import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.batch import Batch  # noqa: F401
from app.models.image import Image  # noqa: F401
from app.models.detection import Detection  # noqa: F401
from app.models.assessment import Assessment  # noqa: F401
from app.models.report import Report  # noqa: F401
