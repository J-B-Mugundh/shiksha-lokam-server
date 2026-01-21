from fastapi import FastAPI
from app.routers.executions import router as executions_router
from app.routers.execution_actions import router as actions_router
from app.routers.corrective_actions import router as corrective_router

app = FastAPI(title="LFA Execution Engine")

app.include_router(executions_router)
app.include_router(actions_router)
app.include_router(corrective_router)
