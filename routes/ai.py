
from fastapi import APIRouter
from models.ai_execution_models import GenerateLevelsRequest
from services.ai_execution_level_service import generate_execution_levels
router=APIRouter(prefix="/ai")
@router.post("/generate-execution-levels")
async def gen(req:GenerateLevelsRequest):
    return await generate_execution_levels(req.lfa_content)
