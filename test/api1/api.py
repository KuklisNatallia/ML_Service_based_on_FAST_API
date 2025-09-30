import routes
from fastapi import FastAPI
from routes.home import home_route
from routes.event import event_router
from routes.user import user_route
from routes.balance import balance_router
from routes.shema import model_router

app = FastAPI()


app.include_router(home_route)
app.include_router(event_router, prefix="/api/events")
app.include_router(user_route, prefix="/api/users")
app.include_router(balance_router, prefix="/api/balance")
app.include_router(model_router, prefix="/api/models")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
