from sqlmodel import Session
from modelses.user import User
from modelses.transaction import Trans, TransactionType
from modelses.balance import Balance


class BalanceService:
    def __init__(self, session: Session):
        self.session = session

    def get_balance(self, user: User) -> float:
        # Возвращает текущий баланс пользователя
        balance = self.session.get(Balance, user.user_id)
        return balance.amount if balance else 0.0

    def deposit(self, user: User, amount: float) -> None:
        balance = self.session.get(Balance, user.user_id)
        if not balance:
            balance = Balance(user_id=user.user_id, amount=0.0)
            self.session.add(balance)
        balance.amount += amount
        self.session.commit()

        #self.session.add(Trans)
        #self.session.commit()

    def admin_deposit(self, user: User, amount: float) -> None:
        pass