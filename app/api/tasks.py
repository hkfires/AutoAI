"""Task CRUD API Routes.

Endpoints will be implemented in Story 2.2: Task Management API.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# CRUD endpoints to be implemented in Story 2.2:
# - POST /api/tasks - Create task
# - GET /api/tasks - List tasks
# - GET /api/tasks/{task_id} - Get task by ID
# - PUT /api/tasks/{task_id} - Update task
# - DELETE /api/tasks/{task_id} - Delete task
