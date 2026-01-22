
from fastapi import APIRouter
from fastapi.responses import FileResponse
from services.export_service import export_lfa
router=APIRouter()
@router.get("/lfas/{lfa_id}/export/{fmt}")
async def export(lfa_id:str,fmt:str):
    path=await export_lfa(lfa_id,fmt)
    return FileResponse(path)
