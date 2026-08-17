from fastapi import APIRouter

from app.api.routes.applications import router as applications_router
from app.api.routes.auth import router as auth_router
from app.api.routes.candidate_intelligence import router as candidate_intelligence_router
from app.api.routes.cvs import router as cvs_router
from app.api.routes.generation import router as generation_router
from app.api.routes.health import router as health_router
from app.api.routes.integrations import router as integrations_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.matches import router as matches_router
from app.api.routes.preferences import router as preferences_router
from app.api.routes.profile import router as profile_router
from app.api.routes.system import router as system_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(preferences_router)
api_router.include_router(cvs_router)
api_router.include_router(applications_router)
api_router.include_router(integrations_router)
api_router.include_router(candidate_intelligence_router)
api_router.include_router(generation_router)
api_router.include_router(jobs_router)
api_router.include_router(matches_router)
api_router.include_router(system_router)
