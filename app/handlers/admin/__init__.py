from aiogram import Router

from app.handlers.admin.panel import router as panel_router
from app.handlers.admin.user_card import router as find_patient_router
from app.handlers.admin.change_dose import router as change_dose_router
from app.handlers.admin.therapy_history import router as therapy_history_router
from app.handlers.admin.user_orders import router as orders_router
from app.filters.is_admin import IsAdmin
from app.handlers.admin.checkins import router as checkins_router
from app.handlers.admin.users import router as users_router
from app.handlers.admin.create_dose import router as create_dose_router
from app.handlers.admin.delete_dose import router as delete_dose_router

router = Router()

router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

router.include_router(panel_router)
router.include_router(delete_dose_router)
router.include_router(create_dose_router)
router.include_router(users_router)
router.include_router(checkins_router)
router.include_router(orders_router)
router.include_router(find_patient_router)
router.include_router(change_dose_router)
router.include_router(therapy_history_router)
