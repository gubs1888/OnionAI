"""ORM models for Onion Quality AI (TEAM B).

Schema overview (see ARCHITECTURE.md):

    User 1 ---* Batch 1 ---* Image 1 ---* Detection
                 Batch 1 ---* Assessment 1 ---* Report
"""

from app.models.user import User  # noqa: F401
from app.models.batch import Batch  # noqa: F401
from app.models.image import Image  # noqa: F401
from app.models.detection import Detection  # noqa: F401
from app.models.assessment import Assessment  # noqa: F401
from app.models.report import Report  # noqa: F401
