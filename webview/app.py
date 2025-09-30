from fastapi import FastAPI, Request, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
import bcrypt
from datetime import datetime
from typing import Optional, List
import json

import modelses, services, database
from modelses.models import MLModelService, PredictionResult, MLModel
from services.balance import BalanceService as ImportedBalanceService
from services.crud.user import get_user_by_email, create_user, get_user_by_id
from modelses.user import User
from modelses.balance import Balance
from database.databases import engine
from database.config import Settings, get_settings
from modelses.transaction import Trans, TransactionType

from services.auth.jwt_handler import create_access_token, verify_access_token, get_current_user_from_token
from services.auth.cookieauth import OAuth2PasswordBearerWithCookie
from services.auth.loginform import LoginForm
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
settings = get_settings()

# Настройка шаблонов и статических файлов
templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")

# OAuth2 схема с куками
oauth2_scheme = OAuth2PasswordBearerWithCookie(
    tokenUrl="/api/users/login",
    auto_error=False
)


class BalanceService:
    def __init__(self, session: Session):
        self.session = session

    def get_balance(self, user: User) -> float:
        balance = self.session.get(Balance, user.user_id)
        if not balance:
            # Создаем баланс если его нет
            balance = Balance(user_id=user.user_id, amount=0.0)
            self.session.add(balance)
            self.session.commit()
            self.session.refresh(balance)
        return balance.amount

    def deposit(self, user: User, amount: float) -> None:
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

    def withdraw(self, user: User, amount: float) -> bool:
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


# получение текущего пользователя
async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    if not token:
        return None

    try:
        user_data = get_current_user_from_token(token)
        with Session(engine) as db_session:
            user = db_session.get(User, user_data["user_id"])
            return user
    except HTTPException:
        return None


# аутентифицированные пользователи
async def get_authenticated_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    user_data = get_current_user_from_token(token)
    with Session(engine) as db_session:
        user = db_session.get(User, user_data["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user


@app.get("/", response_class=HTMLResponse)
async def index(
        request: Request,
        current_user: Optional[User] = Depends(get_current_user)
):
    error_message = request.query_params.get("error")
    success_message = request.query_params.get("success")

    if current_user:
        with Session(engine) as db_session:
            balance_service = BalanceService(db_session)
            balance = balance_service.get_balance(current_user)

            # Проверяем наличие последнего предсказания
            prediction_made = False
            prediction_result = None

            # Получаем последнее предсказание из базы
            statement = select(PredictionResult).where(
                PredictionResult.user_id == current_user.user_id
            ).order_by(PredictionResult.created_at.desc()).limit(1)

            last_prediction = db_session.exec(statement).first()
            if last_prediction:
                prediction_made = True

                prediction_result = last_prediction.get_prediction_rez()

            return templates.TemplateResponse("app.html", {
                "request": request,
                "registered": True,
                "username": current_user.username,
                "balance": balance,
                "prediction_made": prediction_made,
                "prediction_result": prediction_result,
                "error_message": error_message,
                "success_message": success_message
            })

    return templates.TemplateResponse("app.html", {
        "request": request,
        "registered": False,
        "error_message": error_message,
        "success_message": success_message
    })


@app.post("/api/users/register")
async def register(request: Request, response: Response):
    form_data = await request.form()
    username = form_data.get("username", "").strip()
    email = form_data.get("email", "").strip()
    password = form_data.get("password", "").strip()

    # Валидация
    if not all([username, email, password]):
        return RedirectResponse("/?error=Все поля обязательны для заполнения", status_code=303)

    if len(password) < 8:
        return RedirectResponse("/?error=Пароль должен содержать минимум 8 символов", status_code=303)

    if "@" not in email or "." not in email:
        return RedirectResponse("/?error=Некорректный формат email", status_code=303)

    with Session(engine) as db_session:
        # Проверяем, нет ли уже такого пользователя
        existing_user = db_session.exec(select(User).where(User.email == email)).first()
        if existing_user:
            return RedirectResponse("/?error=Пользователь с таким email уже существует", status_code=303)

        # Создаем нового пользователя
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            created_at=datetime.now(),
            balance=0.0
        )

        try:
            db_session.add(new_user)
            db_session.commit()
            db_session.refresh(new_user)

            # Создаем баланс для пользователя
            balance = Balance(user_id=new_user.user_id, amount=0.0)
            db_session.add(balance)
            db_session.commit()

            # Создаем JWT токен
            token = create_access_token(new_user.user_id, new_user.username)

            # Устанавливаем токен в куки
            response = RedirectResponse("/?success=Регистрация завершена успешно!", status_code=303)
            response.set_cookie(
                key=settings.COOKIE_NAME,
                value=token,
                httponly=True,
                max_age=3600,
                secure=not settings.DEBUG,
                samesite="lax"
            )

            return response

        except Exception as e:
            db_session.rollback()
            return RedirectResponse(f"/?error=Ошибка при создании пользователя: {str(e)}", status_code=303)


@app.post("/api/users/login")
async def login(request: Request, response: Response):
    try:
        form_data = await request.form()
        email = form_data.get("username", "").strip()
        password = form_data.get("password", "").strip()

        if not email or not password:
            return RedirectResponse("/?error=Email и пароль обязательны", status_code=303)

        with Session(engine) as db_session:
            user = db_session.exec(select(User).where(User.email == email)).first()
            if not user:
                return RedirectResponse("/?error=Неверный email или пароль", status_code=303)

            # Проверяем пароль
            try:
                if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                    return RedirectResponse("/?error=Неверный email или пароль", status_code=303)
            except Exception as e:
                return RedirectResponse("/?error=Ошибка проверки пароля", status_code=303)

            # Создаем JWT токен
            token = create_access_token(user.user_id, user.username)

            # Устанавливаем токен в куки
            response = RedirectResponse("/?success=Вход выполнен успешно!", status_code=303)
            response.set_cookie(
                key=settings.COOKIE_NAME,
                value=token,
                httponly=True,
                max_age=3600,
                secure=not settings.DEBUG,
                samesite="lax"
            )

            return response

    except Exception as e:
        print(f"Login error: {e}")
        return RedirectResponse(f"/?error=Ошибка сервера: {str(e)}", status_code=303)

@app.post("/balance")
async def handle_balance(
        request: Request,
        current_user: User = Depends(get_authenticated_user)
):
    form_data = await request.form()
    try:
        amount = float(form_data.get("amount", 10))
    except ValueError:
        return RedirectResponse("/?error=Неверная сумма", status_code=303)

    with Session(engine) as db_session:

        balance_service = BalanceService(db_session)
        balance_service.deposit(current_user, amount)

    return RedirectResponse("/?success=Баланс пополнен успешно!", status_code=303)


@app.post("/prediction")
async def handle_prediction(
        request: Request,
        current_user: User = Depends(get_authenticated_user)
):
    form_data = await request.form()

    # Получаем данные из формы
    petal_length = form_data.get("petal_length")
    petal_width = form_data.get("petal_width")

    # Подготовка данных и валидация
    prediction_data = []
    try:
        if petal_length:
            pl = float(petal_length)
            if pl < 0 or pl > 100:
                return RedirectResponse("/?error=Некорректное значение petal_length", status_code=303)
        else:
            pl = None

        if petal_width:
            pw = float(petal_width)
            if pw < 0 or pw > 100:
                return RedirectResponse("/?error=Некорректное значение petal_width", status_code=303)
        else:
            pw = None

        if pl is not None or pw is not None:

            entry = {}
            if pl is not None:
                entry["petal_length"] = pl
            if pw is not None:
                entry["petal_width"] = pw
            prediction_data.append(entry)

    except ValueError:
        return RedirectResponse("/?error=Некорректные данные для предсказания", status_code=303)

    with Session(engine) as db_session:
        balance_service = BalanceService(db_session)
        balance = balance_service.get_balance(current_user)

        # Стоимость предсказания из ML модели
        ml_model = MLModel()
        cost = ml_model.get_cost_predict()

        # Проверяем баланс
        if balance < cost:
            return RedirectResponse("/?error=Недостаточно средств для предсказания", status_code=303)

        success_withdraw = balance_service.withdraw(current_user, cost)
        if not success_withdraw:
            return RedirectResponse("/?error=Недостаточно средств для предсказания", status_code=303)

        #user_balance_obj = Balance(user_id=current_user.user_id, amount=balance)
        ml_service = MLModelService(balance_service=balance_service)

        try:
            prediction_result = ml_service.make_prediction(current_user, prediction_data)

            # Сохраняем результат в базу
            if prediction_result:
                prediction = PredictionResult(
                    user_id=current_user.user_id,
                    prediction_rez=json.dumps(prediction_result),
                    cost=cost,
                    created_at=datetime.now()
                )
                db_session.add(prediction)
                db_session.commit()

            return RedirectResponse("/?success=Предсказание выполнено успешно!", status_code=303)

        except Exception as e:
            db_session.rollback()
            return RedirectResponse(f"/?error=Ошибка предсказания: {str(e)}", status_code=303)

@app.post("/logout")
async def logout(response: Response):
    # Очищаем куки
    response = RedirectResponse("/?success=Выход выполнен успешно!", status_code=303)
    response.delete_cookie(settings.COOKIE_NAME)
    return response


@app.get("/api/predictions")
async def get_user_predictions(
        current_user: User = Depends(get_authenticated_user)
):
    # API для получения предсказаний пользователя
    with Session(engine) as db_session:
        statement = select(PredictionResult).where(
            PredictionResult.user_id == current_user.user_id
        ).order_by(PredictionResult.created_at.desc())

        predictions = db_session.exec(statement).all()
        return {
            "predictions": [
                {
                    "id": pred.prediction_id,
                    "result": pred.get_prediction_rez(),
                    "cost": pred.cost,
                    "created_at": pred.created_at
                } for pred in predictions
            ]
        }


@app.get("/api/user/balance")
async def get_user_balance(
        current_user: User = Depends(get_authenticated_user)
):
    # API для получения баланса пользователя
    with Session(engine) as db_session:
        balance_service = BalanceService(db_session)
        balance = balance_service.get_balance(current_user)
        return {"balance": balance}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.app_host,
        port=int(settings.app_port),
        #reload=True,
        log_level="debug"
    )