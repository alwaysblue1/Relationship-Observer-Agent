import asyncio
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_user
from app.models.chat import AnalysisSession, AnonymizedMessage, Participant, MessageType
from app.models.user import User
from app.services.parser import ChatParser
from app.services.anonymizer import Anonymizer
from app.services.event_engine import RelationshipEventEngine
from app.services.observer import ObserverService

router = APIRouter(prefix="/api/upload", tags=["upload"])


def _decode_with_best_encoding(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("gbk", errors="replace")


@router.post("/chat")
async def upload_chat(
    file: UploadFile = File(...),
    platform: str = Form("wechat"),
    self_name: str = Form("me"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    if file.filename is None:
        raise HTTPException(400, "Filename is required")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "txt"
    if ext not in ("txt", "json"):
        raise HTTPException(400, "Only .txt and .json files are supported")

    raw_bytes = await file.read()
    content = _decode_with_best_encoding(raw_bytes)
    if not content.strip():
        raise HTTPException(400, "File is empty")

    detected_platform = ChatParser.detect_platform(file.filename)
    if platform == "auto":
        platform = detected_platform.value

    raw_messages = ChatParser.parse(content, file.filename)
    if not raw_messages:
        raise HTTPException(400, "No messages could be parsed from the file")

    anon = Anonymizer()
    anonymized = []
    for msg in raw_messages:
        anon_text, anon_sender = anon.anonymize(
            msg.get("content", ""),
            msg.get("sender", "Unknown"),
        )
        anonymized.append({
            **msg,
            "anonymized_content": anon_text,
            "anon_sender": anon_sender,
        })

    session = AnalysisSession(
        id=str(uuid4()),
        title=file.filename.rsplit(".", 1)[0],
        platform=detected_platform.value,
        total_messages=len(anonymized),
        user_id=current_user.id,
    )

    participants_seen = {}
    for msg in anonymized:
        sid = msg["anon_sender"]
        if sid not in participants_seen:
            is_self = msg["sender"] == self_name or self_name.lower() in msg["sender"].lower()
            participants_seen[sid] = is_self
            participant = Participant(
                session_id=session.id,
                anonymous_id=sid,
                is_self=is_self,
                original_name=msg["sender"] if is_self else None,
            )
            db.add(participant)

    dates = []
    for msg in anonymized:
        try:
            dates.append(datetime.fromisoformat(msg["timestamp"]))
        except (ValueError, KeyError):
            pass
    if dates:
        dates.sort()
        session.date_range_start = dates[0]
        session.date_range_end = dates[-1]

    db.add(session)
    await db.commit()

    for msg in anonymized:
        db_msg = AnonymizedMessage(
            session_id=session.id,
            sender_anon_id=msg["anon_sender"],
            message_type=msg.get("type", MessageType.TEXT.value),
            anonymized_content=msg.get("anonymized_content", ""),
            original_timestamp=datetime.fromisoformat(msg["timestamp"]),
            extra_data={"original_type": msg.get("type"), "original_sender_hash": hash(msg.get("sender", ""))},
        )
        db.add(db_msg)

    await db.commit()

    events = RelationshipEventEngine.detect(anonymized)
    for event in events:
        from app.models.chat import RelationshipEvent as RE
        db_event = RE(
            session_id=session.id,
            event_type=event["event_type"],
            weight=event["weight"],
            description=event["description"],
            occurred_at=datetime.fromisoformat(event["occurred_at"]),
            extra_data=event.get("metadata"),
        )
        db.add(db_event)

    await db.commit()

    analysis = await ObserverService.run_full_analysis(
        session_id=session.id,
        session=session,
        messages=anonymized,
        events=events,
        db=db,
    )

    return {
        "session_id": session.id,
        "title": session.title,
        "platform": session.platform,
        "total_messages": session.total_messages,
        "date_range_start": session.date_range_start.isoformat() if session.date_range_start else None,
        "date_range_end": session.date_range_end.isoformat() if session.date_range_end else None,
        "participants": [{"anon_id": sid, "is_self": is_self} for sid, is_self in participants_seen.items()],
        "event_summary": {
            "total_events": len(events),
            "event_types": list(set(e["event_type"] for e in events)),
            "total_score": sum(e["weight"] for e in events),
        },
        "analysis_id": analysis.id,
    }
