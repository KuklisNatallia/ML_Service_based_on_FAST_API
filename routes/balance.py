import modelses, services, services
from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session
from typing import Dict
from modelses.user import User
from modelses.balance import Balance, BalanceUpdate
from services.balance import BalanceService
from database.databases import get_session
import logging


balance_router = APIRouter()
logger = logging.getLogger(__name__)

@balance_router.get(
    "/{user_id}",
    response_model=Dict[str, float],
    summary="Баланс пользователя",
    description="Баланс пользователя",
    responses={
        200: {"description": "Баланс успешно получен"},
        404: {"description": "Пользователь не найден"}
    }
)
async def get_balance(
        user_id: int,
        balance_service: BalanceService = Depends(lambda: BalanceService())
) -> Dict[str, float]:
    try:
        user = User(id=user_id)
        balance = balance_service.get_balance(user)
        return {"balance": balance}
    except Exception as e:
        logger.error(f"Ошибка при получении баланса: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении баланса"
        )


@balance_router.post(
    "/deposit",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Пополнить баланс",
    description="Пополнение баланса пользователя",
    responses={200: {"description": "Баланс успешно пополнен"}}
)
async def deposit_up(
        data: BalanceUpdate,
        balance_service: BalanceService = Depends(lambda: BalanceService())
) -> Dict[str, str]:
    try:
        user = User(id=data.user_id)
        balance_service.deposit(user, data.amount)
        logger.info(f"Баланс пользователя {data.user_id} пополнен на сумму {data.amount}")
        return {"message": "Баланс успешно пополнен"}
    except Exception as e:
        logger.error(f"Ошибка при пополнении баланса: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при пополнении баланса"
        )

@balance_router.post(
    "/reduction",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Списать средства",
    description="Списание средств с баланса пользователя",
    responses={
        200: {"description": "Средства успешно списаны"},
        402: {"description": "Недостаточно средств"}
    }
)
async def balance_reduction(
        data: BalanceUpdate,
        session: Session = Depends(get_session),
        balance_service: BalanceService = Depends(lambda: BalanceService())
) -> Dict[str, str]:
    try:
        user = User(id=data.user_id)
        current_balance = balance_service.get_balance(user)

        if current_balance < data.amount:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Недостаточно средств"
            )

        # Списание средств
        balance_service.deposit(user, -data.amount)

        logger.info(f"Списание с баланса пользователя {data.user_id} суммы {data.amount}")
        return {"message": "Средства успешно списаны"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при списании средств: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при списании средств"
        )