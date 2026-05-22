import json
import re
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.models.chat import MessageType, Platform


class ChatParser:
    """Parse exported WeChat/QQ chat logs in txt or json format."""

    # New QQ: "昵称: 2024-02-28 14:11:21" or "昵称: 05-21 13:12:51"
    QQ_HEADER_RE = re.compile(
        r'^(.+?)[:：]\s*((?:\d{2,4}[-/])?\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)$'
    )
    # Old QQ: "昵称 2025/10/15 18:42:40" (space separator, always full Y/M/D H:M:S with slashes)
    QQ_OLD_HEADER_RE = re.compile(
        r'^(.+?)\s+(\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}:\d{2})$'
    )
    WECHAT_HEADER_RE = re.compile(
        r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?\s+(.+?)[:：]\s*(.*)$'
    )
    IMG_TAG_RE = re.compile(r'<img\s+src="([^"]*)"[^>]*/?>', re.IGNORECASE)

    SYSTEM_EVENTS = {
        "加入了群聊", "退出了群聊", "撤回了一条消息", "修改群名为",
        "邀请", "移出了群聊", "开启了朋友验证", "关闭了朋友验证",
        "你已添加了", "以上是打招呼的内容", "修改了群公告",
    }

    @staticmethod
    def detect_platform(filename: str) -> Platform:
        name_lower = filename.lower()
        if "wechat" in name_lower or "微信" in name_lower:
            return Platform.WECHAT
        if "qq" in name_lower:
            return Platform.QQ
        return Platform.WECHAT

    @classmethod
    def parse(cls, content: str, filename: str) -> list[dict]:
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"
        if ext == "json":
            return cls._parse_json(content)
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        if cls._detect_qq_format(normalized):
            return cls._parse_txt_qq(normalized)
        return cls._parse_txt_wechat(normalized)

    @classmethod
    def _detect_qq_format(cls, content: str) -> bool:
        lines = [l.strip() for l in content.split("\n") if l.strip()][:30]
        qq_count = 0
        wechat_count = 0
        for line in lines:
            if cls.QQ_HEADER_RE.match(line) or cls.QQ_OLD_HEADER_RE.match(line):
                qq_count += 1
            if cls.WECHAT_HEADER_RE.match(line):
                wechat_count += 1
        return qq_count > wechat_count

    @classmethod
    def _parse_txt_qq(cls, content: str) -> list[dict]:
        results = []
        last_full_year: Optional[int] = None

        for block in content.strip().split("\n\n"):
            block = block.strip()
            if not block:
                continue

            block_lines = block.split("\n")
            first_line = block_lines[0].strip()

            header_match = cls.QQ_HEADER_RE.match(first_line) or cls.QQ_OLD_HEADER_RE.match(first_line)
            if not header_match:
                continue

            sender = header_match.group(1).strip()
            date_str = header_match.group(2).strip()

            content_lines = []
            for line in block_lines[1:]:
                line = line.strip()
                if not line:
                    continue
                cleaned = cls._clean_img_tags(line)
                if cleaned.strip():
                    content_lines.append(cleaned.strip())

            content_text = "\n".join(content_lines) if content_lines else ""

            ts = cls._parse_qq_datetime(date_str, last_full_year)
            if ts:
                if ts.year:
                    last_full_year = ts.year

            msg_type = cls._detect_message_type(content_text)

            results.append({
                "id": str(uuid4()),
                "timestamp": ts.isoformat() if ts else datetime.utcnow().isoformat(),
                "sender": sender,
                "content": content_text,
                "type": msg_type.value,
            })

        return results

    @classmethod
    def _clean_img_tags(cls, text: str) -> str:
        def _replace(m: re.Match) -> str:
            path = m.group(1)
            if "Emoji" in path or "emoji" in path:
                return "[表情]"
            return "[图片]"
        return cls.IMG_TAG_RE.sub(_replace, text)

    @classmethod
    def _parse_qq_datetime(cls, date_str: str, last_year: Optional[int]) -> Optional[datetime]:
        formats = [
            ("%Y-%m-%d %H:%M:%S", True),
            ("%Y-%m-%d %H:%M", True),
            ("%Y/%m/%d %H:%M:%S", True),
            ("%Y/%m/%d %H:%M", True),
            ("%m-%d %H:%M:%S", False),
            ("%m-%d %H:%M", False),
            ("%m/%d %H:%M:%S", False),
            ("%m/%d %H:%M", False),
        ]
        for fmt, has_year in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if not has_year:
                    year = last_year or datetime.utcnow().year
                    dt = dt.replace(year=year)
                return dt
            except ValueError:
                continue
        return None

    @classmethod
    def _parse_json(cls, content: str) -> list[dict]:
        data = json.loads(content)
        if isinstance(data, dict):
            messages = data.get("messages") or data.get("message") or data.get("msgs") or []
        else:
            messages = data if isinstance(data, list) else []

        results = []
        for msg in messages:
            parsed = cls._normalize_json_message(msg)
            if parsed:
                results.append(parsed)
        return results

    @classmethod
    def _normalize_json_message(cls, msg: dict) -> Optional[dict]:
        ts = msg.get("timestamp") or msg.get("time") or msg.get("createTime")
        if ts is None:
            return None
        try:
            if isinstance(ts, (int, float)):
                dt = datetime.fromtimestamp(ts / 1000 if ts > 1e12 else ts)
            else:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except (ValueError, OSError):
            return None

        content = str(msg.get("content") or msg.get("text") or msg.get("message") or "")
        sender = str(msg.get("sender") or msg.get("senderName") or msg.get("talker") or "Unknown")

        msg_type = cls._detect_message_type(content, msg.get("type") or msg.get("msgType"))

        return {
            "id": str(uuid4()),
            "timestamp": dt.isoformat(),
            "sender": sender,
            "content": content,
            "type": msg_type.value,
            "raw": msg,
        }

    @classmethod
    def _parse_txt_wechat(cls, content: str) -> list[dict]:
        results = []
        current_msg = None
        current_sender = None
        current_ts = None
        current_lines = []

        def flush():
            nonlocal current_msg, current_sender, current_ts, current_lines
            if current_msg is not None and current_sender and current_ts:
                text = "\n".join(current_lines)
                results.append({
                    "id": str(uuid4()),
                    "timestamp": current_ts.isoformat(),
                    "sender": current_sender,
                    "content": text,
                    "type": cls._detect_message_type(text).value,
                })
            current_msg = None
            current_sender = None
            current_ts = None
            current_lines = []

        for line in content.strip().split("\n"):
            if not line.strip():
                continue

            parts = line.split(None, 2)
            if len(parts) < 3:
                is_system = any(evt in line for evt in cls.SYSTEM_EVENTS)
                if is_system:
                    flush()
                    results.append({
                        "id": str(uuid4()),
                        "timestamp": datetime.utcnow().isoformat(),
                        "sender": "SYSTEM",
                        "content": line.strip(),
                        "type": MessageType.SYSTEM_EVENT.value,
                    })
                elif current_lines:
                    current_lines.append(line.strip())
                continue

            date_str, time_str, rest = parts[0], parts[1], parts[2]

            try:
                ts = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    ts = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                except ValueError:
                    try:
                        ts = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M:%S")
                    except ValueError:
                        try:
                            ts = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M")
                        except ValueError:
                            current_lines.append(line.strip())
                            continue

            match = re.match(r'^(.+?)[:：]\s*(.*)$', rest)
            if match:
                flush()
                current_msg = 1
                current_sender = match.group(1).strip()
                current_lines = [match.group(2).strip()]
                current_ts = ts
            else:
                is_system = any(evt in rest for evt in cls.SYSTEM_EVENTS)
                if is_system:
                    flush()
                    results.append({
                        "id": str(uuid4()),
                        "timestamp": ts.isoformat(),
                        "sender": "SYSTEM",
                        "content": rest.strip(),
                        "type": MessageType.SYSTEM_EVENT.value,
                    })
                else:
                    current_lines.append(rest.strip())
                    if current_ts is None:
                        current_ts = ts

        flush()
        return results

    @classmethod
    def _detect_message_type(cls, content: str, type_hint: Optional[str] = None) -> MessageType:
        if type_hint:
            type_lower = type_hint.lower()
            if "image" in type_lower or "img" in type_lower or "图片" in type_lower:
                return MessageType.IMAGE
            if "voice" in type_lower or "audio" in type_lower:
                return MessageType.VOICE_CALL
            if "video" in type_lower:
                return MessageType.VIDEO_CALL
            if "system" in type_lower or "event" in type_lower:
                return MessageType.SYSTEM_EVENT
            if "emoji" in type_lower or "sticker" in type_lower:
                return MessageType.EMOJI

        content_stripped = content.strip()
        if content_stripped in ["[图片]", "[Image]", "[Photo]", "[表情]", "[Sticker]", "[动画表情]"]:
            return MessageType.IMAGE
        if content_stripped in ["[语音]", "[Voice]", "[语音通话]", "[Voice Call]"]:
            return MessageType.VOICE_CALL
        if content_stripped in ["[视频]", "[Video]", "[视频通话]", "[Video Call]"]:
            return MessageType.VIDEO_CALL
        if content_stripped in ["[系统消息]", "[System]"]:
            return MessageType.SYSTEM_EVENT

        emoji_only = re.match(r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF☀-⛿✀-➿︀-️‍]+$', content_stripped)
        if emoji_only:
            return MessageType.EMOJI

        return MessageType.TEXT
