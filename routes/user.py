import database, services, modelses
from fastapi import APIRouter, HTTPException, status, Depends
from database.databases import get_session
from modelses.user import User
from services.crud import user as UserService
from pydantic import BaseModel
from typing import List, Dict
import logging
from sqlmodel import Session

# Для безопасного хеширования паролей используем passlib
from passlib.context import CryptContext


# Настройка логирования
logger = logging.getLogger(__name__)

@staticmethod
def hash_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def validate_password(self, password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

# Pydantic модель для входных данных при регистрации и входе
class UserCreateSchema(BaseModel):
    email: str
    password: str
    username: str

user_route = APIRouter()

@user_route.post(
    '/signup',
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
    description="Регистрация нового пользователя с email и паролем"
)
async def signup(data: UserCreateSchema, session=Depends(get_session)) -> Dict[str, str]:
    try:
        # Проверка существования пользователя по email
        existing_user = UserService.get_user_by_email(data.email, session)
        if existing_user:
            logger.warning(f"Попытка регистрации с существующим email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с этим email уже существует"
            )

        # Хеширование пароля перед сохранением
        password_hash = hash_password(data.password)

        # Создание нового пользователя
        user = User(
            email=data.email,
            password_hash=password_hash,
            username=data.username
        )

        UserService.create_user(user, session)
        logger.info(f"Новый пользователь зарегистрирован: {data.email}")
        return {"message": "Пользователь успешно зарегистрирован"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при регистрации: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании пользователя"
        )

@user_route.post('/signin')
async def signin(data: UserCreateSchema, session=Depends(get_session)) -> Dict[str, str]:
    try:
        user = UserService.get_user_by_email(data.email, session)
        if user is None:
            logger.warning(f"Попытка входа с несуществующим email: {data.email}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        # Проверка пароля с помощью безопасного сравнения
        if not validate_password(data.password, user.password_hash):
            logger.warning(f"Неудачная попытка входа пользователя: {data.email}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Неверные учетные данные")

        return {"message": "Пользователь успешно авторизован"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при входе: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при авторизации"
        )

@user_route.get(
    "/get_all_users",
    response_model=List[User],
    summary="Получить всех пользователей",
    response_description="Список пользователей"
)
async def get_all_users(session=Depends(get_session)) -> List[User]:
    try:
        users = UserService.get_all_users(session)
        logger.info(f"Получено {len(users)} пользователей")
        return users
    except Exception as e:
        logger.error(f"Ошибка при получении пользователей: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении пользователей"
        )