from fastapi import APIRouter, Depends
from app.services.result_service import ResultService
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/executions/{execution_id}/actions",
    tags=["Execution Actions"]
)

result_service = ResultService()

@router.post("/{action_id}/results", status_code=201)
async def submit_action_results(
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
    )
