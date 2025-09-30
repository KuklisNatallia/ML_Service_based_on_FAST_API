import modelses
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Tuple
import re
from sqlmodel import SQLModel, Field, Relationship
from modelses.balance import Balance, BalanceService
from modelses.user import User
import json
import random
import numpy as np
from sklearn import datasets
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import pandas as pd


class MLModel(): # Класс ML модели
    def __init__(self):
        self._model = None
        self._is_trained = False
        self._train_model()

    def _train_model(self):
        # Обучение модели
        if self._is_trained:
            return

        data = datasets.load_iris()
        df = pd.DataFrame(data.data, columns=data.feature_names)
        df['target'] = data.target

        # Используем только petal length и petal width (столбцы 2 и 3)
        X = df.iloc[:, [2, 3]].values
        y = df['target'].values

        # Разделяем данные
        X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.5, random_state=42
        )

        # Обучаем модель
        self._model = LogisticRegression()
        self._model.fit(X_train, y_train)
        self._is_trained = True

    def predict(self, data: List[Dict]) -> List[Dict]:
        # Случайный цвет для каждого элемента
        # colors = ["красный", "синий", "желтый", "зеленый", "фиолетовый"]
        # return [{"color": random.choice(colors)} for _ in data]
        #return [{"prediction": "example"} for i in data]

        # Предсказание цвета лепестка ириса
        if not self._is_trained:
            self._train_model()

        if not data:
            return []

        # Преобразуем входные данные в формат для модели
        features = []
        for item in data:
            # Ожидаем данные в формате: [{"petal_length": 1.4, "petal_width": 0.2}, ...]
            petal_length = item.get('petal_length', 0.0)
            petal_width = item.get('petal_width', 0.0)
            features.append([petal_length, petal_width])

        # Делаем предсказание
        predictions = self._model.predict(features)

        # Преобразуем числовые предсказания в названия цветов
        result = []
        classes = ["setosa", "versicolor", "virginica"]
        for pred in predictions:
            label = classes[int(pred)] if 0 <= int(pred) < len(classes) else "unknown"
            result.append({"color": label})

        return result


    def get_cost_predict(self) -> float:
        # Стоимость предсказания
        return 10.0

    def reset_training(self) -> None:
        # Сброс обучения модели для возможности переобучения
        self._is_trained = False
        self._model = None

class PredictionResult (SQLModel, table=True):
    prediction_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.user_id")
    prediction_rez: str # JSON строка
    cost: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional["User"] = Relationship(back_populates="predictions")

    def get_prediction_rez(self) -> List[Dict]:
        return json.loads(self.prediction_rez)

    def set_prediction_rez(self, data: List[Dict]):
        self.prediction_rez = json.dumps(data)

class Predictions:
    def __init__(self, ml_model: MLModel, balance: Balance):
        self.ml_model = ml_model
        self.balance=balance

    def make_predict(self, user: User, data: List[Dict]) -> PredictionResult:
        # Проверка баланса достаточности средств пользователя
        cost = self.ml_model.get_cost_predict()
        user_balance = self.balance.get_balance(user)
        if user_balance < cost:
            raise ValueError("Not enough credits")

        # Выполнение предсказания
        predictions = self.ml_model.predict(data)

        # Создание записи о предсказании
        prediction_result = PredictionResult(
            prediction_id=None,
            user_id=user.user_id,
            prediction_rez=json.dumps(predictions),
            cost=cost
        )

        # Списание средств
        self.balance.deposit(user, -cost)
        return prediction_result

class MLModelService:
    def __init__(self, balance_service: BalanceService):
        # Инициализация модели Iris
        self.imodel = MLModel()
        self.balance_service = balance_service
        #self.predictions = (Predictions(self.imodel, balance))

    def make_prediction(self, user: User, data: List[Dict]) -> List[Dict]:
        cost = self.imodel.get_cost_predict()

        # Используем методы объекта balance_service
        balance = self.balance_service.get_balance(user)
        if balance < cost:
            raise ValueError("Not enough credits")

        predictions = self.imodel.predict(data)

        # Списание средств (нужно передать session)
        # self.balance_obj.update_balance(-cost, session)
        success = self.balance_service.withdraw(user, cost)
        if not success:
            raise ValueError("Withdrawal failed")
        return predictions

        #prediction_result = self.predictions.make_predict(user, data)
        #return prediction_result.get_prediction_rez()

    def reset_model(self) -> None:
        # Сброс модели для переобучения
        self.ml_model.reset_training()
