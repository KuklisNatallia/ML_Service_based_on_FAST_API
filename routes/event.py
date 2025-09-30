import modelses, database
from fastapi import APIRouter, Body, HTTPException, status, Depends
from database.databases import get_session
from modelses.event import Event
from typing import List


event_router = APIRouter()
events = []

@event_router.get("/", response_model=List[Event])
async def get_all_events() -> List[Event]:
    return events

@event_router.post("/new")
async def create_event(body: Event = Body(...)) -> dict:
    events.append(body)
    return {"message": "Событие успешно создано"}
