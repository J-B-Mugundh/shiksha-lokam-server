from fastapi import APIRouter, Depends
from app.services.corrective_service import CorrectiveService
from app.services.result_service import ResultService
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/executions/{execution_id}/actions/{action_id}/corrective",
    tags=["Corrective Actions"]
)

corrective_service = CorrectiveService()
result_service = ResultService()

@router.get("")
async def get_corrective(
    action_id: str,
    user=Depends(get_current_user),
):
    return await corrective_service.get_for_action(action_id)


@router.post("/accept")
async def accept_corrective(
    corrective_id: str,
    user=Depends(get_current_user),
):
    return await corrective_service.accept(corrective_id)


@router.post("/results", status_code=201)
async def submit_corrective_results(
    execution_id: str,
    action_id: str,
    payload: dict,
    user=Depends(get_current_user),
):
    return await result_service.submit_results(
        execution_id=execution_id,
        action_id=action_id,
        payload=payload,
        user=user,
        is_corrective=True,
    )
