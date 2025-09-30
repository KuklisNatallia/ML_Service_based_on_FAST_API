import modelses, services, database
from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session
from typing import List, Dict
from modelses.models import MLModel, PredictionResult
from database.databases import get_session
import logging, random

model_router = APIRouter()
logger = logging.getLogger(__name__)

# Цвета лепестков
COLORS = ["красный", "синий", "желтый", "зеленый", "фиолетовый", "розовый"]


@model_router.get(
    "/",
    response_model=List[MLModel],
    summary="Получить информацию о модели",
    description="Получить информацию о модели предсказания цвета лепестка",
    responses={
        200: {"description": "Информация о модели получена"},
        500: {"description": "Ошибка сервера"}
    }
)
async def get_models(
        session: Session = Depends(get_session)
) -> List[MLModel]:
    try:
        return [
            MLModel(id=1, name="Цвет лепестка", description="Модель предсказывает случайный цвет лепестка цветка")
        ]
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении информации о модели"
        )

@model_router.post(
    "/predict",
    response_model=PredictionResult,
    status_code=status.HTTP_200_OK,
    summary="Предсказать цвет лепестка",
    description="Получить предсказание цвета лепестка цветка",
    responses={
        200: {"description": "Предсказание выполнено успешноl"},
        402: {"description": "Недостаточно средств"}
    }
)
async def make_prediction(
        request: PredictionResult,
        session: Session = Depends(get_session)
) -> PredictionResult:
    try:
        # 1. Проверка баланса пользователя
        # 2. Выполнение предсказания
        # 3. Списание средств
        # 4. Сохранение результата

        logger.info(f"Запрос на предсказание от пользователя {request.user_id}")
        # Случайное предсказание
        prediction = {
            "color": random.choice(COLORS),
            "confidence": round(random.uniform(0.7, 1.0), 2)
        }
        return PredictionResult(
            success=True,
            prediction=prediction,
            cost=10.0
        )
    except Exception as e:
        logger.error(f"Ошибка при выполнении предсказания: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при выполнении предсказания"
        )