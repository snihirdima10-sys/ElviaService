from aiogram import Router

from app.handlers.user.start import router as start_router
from app.handlers.user.registration import router as registration_router
from app.handlers.user.therapy import router as therapy_router
from app.handlers.user.questionnaire import router as questionnaire_router
from app.handlers.user.progress import router as progress_router
from app.handlers.user.update_weight import router as update_weight_router
from app.handlers.user.create_order import router as create_order_router
from app.handlers.user.my_orders import router as my_orders_router
from app.handlers.user.contact_doctor import router as contact_doctor_router
from app.handlers.user.useful_info import router as useful_info_router


router = Router()

router.include_router(start_router)
router.include_router(registration_router)
router.include_router(therapy_router)
router.include_router(questionnaire_router)
router.include_router(progress_router)
router.include_router(update_weight_router)
router.include_router(create_order_router)
router.include_router(my_orders_router)
router.include_router(contact_doctor_router)
router.include_router(useful_info_router)