"""Service layer: inference, preprocessing, measurement, grading, URS, reports, auth.

Modularity rule: the backend NEVER imports YOLO/torch directly.
All ML access goes through `services/inference.py::analyze_image()`.
"""
