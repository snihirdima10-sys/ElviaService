from aiogram import Router

from app.handlers.admin.panel import router as panel_router
from app.handlers.admin.find_patient import router as find_patient_router
from app.handlers.admin.change_dose import router as change_dose_router
from app.handlers.admin.therapy_history import router as therapy_history_router
from app.handlers.admin.orders import router as orders_router

router = Router()

router.include_router(panel_router)
router.include_router(find_patient_router)
router.include_router(change_dose_router)
router.include_router(therapy_history_router)
router.include_router(orders_router)