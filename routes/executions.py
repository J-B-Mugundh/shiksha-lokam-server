from fastapi import APIRouter, Depends
from app.services.execution_service import ExecutionService
from app.services.level_service import LevelService
from app.services.action_service import ActionService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/executions", tags=["Executions"])

execution_service = ExecutionService()
level_service = LevelService()
action_service = ActionService()

from app.models.execution import CreateExecutionRequest, ExecutionResponse


@router.post("", status_code=201)
async def create_execution(
    payload: CreateExecutionRequest,
    user=Depends(get_current_user),
):
    return await execution_service.create_execution(payload, user)

@router.get("")
async def list_executions(
    filters=Depends(),
    pagination=Depends(),
    user=Depends(get_current_user),
):
    return await execution_service.list(filters, pagination, user)


@router.get("/{execution_id}")
async def get_execution(
    execution_id: str,
    user=Depends(get_current_user),
):
    return await execution_service.get(execution_id)


@router.get("/{execution_id}/levels")
async def get_levels(
    execution_id: str,
    user=Depends(get_current_user),
):
    return await level_service.get_levels(execution_id)


@router.get("/{execution_id}/current-action")
async def get_current_action(
    execution_id: str,
    user=Depends(get_current_user),
):
    return await action_service.get_current_action(execution_id)


@router.post("/{execution_id}/pause")
async def pause_execution(
    execution_id: str,
    user=Depends(get_current_user),
):
    await execution_service.pause(execution_id)
    return {"status": "paused"}


@router.post("/{execution_id}/resume")
async def resume_execution(
    execution_id: str,
    user=Depends(get_current_user),
):
    await execution_service.resume(execution_id)
    return {"status": "active"}


@router.post("/{execution_id}/abandon")
async def abandon_execution(
    execution_id: str,
    user=Depends(get_current_user),
):
    await execution_service.abandon(execution_id)
    return {"status": "abandoned"}
