from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from sqlalchemy.orm import Session
from modelses.transaction import Trans, TransactionType
from datetime import datetime

class Balance(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.user_id", primary_key=True)
    amount: float = Field(default=0.0)

    def update_balance(self, amount: float, session: Session) -> None:
        # Обновление баланса пользователя
        self.amount += amount
        session.add(self)
        session.commit()

    def has_enough_credits(self, amount: float) -> bool:
        # Проверка, достаточно ли средств на балансе
        return self.amount >= amount

class BalanceUpdate(BaseModel):
    # Модель для запроса на изменение баланса
    user_id: int
    amount: float

class BalanceService:
    def __init__(self, session: Session):
        self.session = session

    def get_balance(self, user) -> float:
        balance = self.session.get(Balance, user.user_id)
        if not balance:
            # Создаем баланс если его нет
            balance = Balance(user_id=user.user_id, amount=0.0)
            self.session.add(balance)
            self.session.commit()
            self.session.refresh(balance)
        return balance.amount

    def deposit(self, user, amount: float) -> None:
        balance = self.session.get(Balance, user.user_id)
        if not balance:
            balance = Balance(user_id=user.user_id, amount=amount)
        else:
            balance.amount += amount

        self.session.add(balance)

        # Создаем запись о транзакции
        transaction = Trans(
            transaction_id=f"trans_{datetime.now().timestamp()}",
            user_id=user.user_id,
            amount=amount,
            transaction_type=TransactionType.DEPOSIT.value
        )
        self.session.add(transaction)
        self.session.commit()

    def withdraw(self, user, amount: float) -> bool:
        balance = self.session.get(Balance, user.user_id)
        if not balance or balance.amount < amount:
            return False

        balance.amount -= amount
        self.session.add(balance)

        # Создаем запись о транзакции
        transaction = Trans(
            transaction_id=f"trans_{datetime.now().timestamp()}",
            user_id=user.user_id,
            amount=-amount,
            transaction_type=TransactionType.COST_PREDICTION.value
        )
        self.session.add(transaction)
        self.session.commit()
        return True