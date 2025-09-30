import modelses
from modelses.event import Event
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

def get_all_events(session: Session) -> List[Event]:

    try:
        statement = select(Event)
        events = session.exec(statement).all()
        return events
    except SQLAlchemyError as e:
        session.rollback()
        raise ValueError(f"Database error while fetching events: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")

def get_event_by_id(event_id: int, session: Session) -> Optional[Event]:

    try:
        event = session.get(Event, event_id)
        return event
    except SQLAlchemyError as e:
        session.rollback()
        raise ValueError(f"Database error while fetching event by ID: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")


def create_event(event_data: Event, session: Session) -> Event:

    try:
        session.add(event_data)
        session.commit()
        session.refresh(event_data)
        return event_data
    except SQLAlchemyError as e:
        session.rollback()
        raise ValueError(f"Database error while creating event: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")


def delete_event(event_id: int, session: Session) -> bool:

    try:
        event = session.get(Event, event_id)
        if not event:
            return False

        session.delete(event)
        session.commit()
        return True
    except SQLAlchemyError as e:
        session.rollback()
        raise ValueError(f"Database error while deleting event: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")


def delete_all_events(session: Session) -> int:

    try:
        events = session.exec(select(Event)).all()
        count = len(events)

        for event in events:
            session.delete(event)

        session.commit()
        return count
    except SQLAlchemyError as e:
        session.rollback()
        raise ValueError(f"Database error while deleting all events: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")


def update_event(event_id: int, new_data: dict, session: Session) -> Optional[Event]:
    try:
         event = session.get(Event, event_id)
         if not event:
            return None

         for key, value in new_data.items():
             setattr(event, key, value)

         session.add(event)
         session.commit()
         session.refresh(event)
         return event
    except SQLAlchemyError as e:
        session.rollback()
        raise ValueError(f"Database error while updating event: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")