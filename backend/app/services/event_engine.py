from datetime import datetime, timedelta
from typing import Optional

from app.models.chat import MessageType


EVENT_DEFINITIONS = {
    "start_new_topic": {"weight": 5, "description": "主动开启新话题"},
    "long_text": {"weight": 4, "description": "长文本消息（>100字）"},
    "instant_reply": {"weight": 3, "description": "秒回（<1分钟）"},
    "goodnight": {"weight": 2, "description": "晚安互动"},
    "video_call": {"weight": 8, "description": "视频通话"},
    "late_night_voice": {"weight": 10, "description": "深夜语音通话"},
    "read_but_no_reply_long": {"weight": -6, "description": "已读长时间未回复（>6小时）"},
    "cold_replies": {"weight": -4, "description": "连续简短敷衍回复"},
    "cold_start_fail": {"weight": -8, "description": "冷启动失败"},
    "image_share": {"weight": 3, "description": "分享图片"},
    "emoji_dense": {"weight": 2, "description": "高密度表情包互动"},
    "late_night_interaction": {"weight": 6, "description": "深夜互动（0-5点）"},
    "morning_greeting": {"weight": 3, "description": "早安问候"},
    "long_conversation": {"weight": 5, "description": "长对话（连续20+轮）"},
    "question_asked": {"weight": 3, "description": "主动提问/关心"},
    "repaired_after_conflict": {"weight": 7, "description": "冲突后修复行为"},
}


class RelationshipEventEngine:
    """Detects relationship events from anonymized chat messages."""

    @staticmethod
    def detect(messages: list[dict]) -> list[dict]:
        if not messages:
            return []

        sorted_msgs = sorted(messages, key=lambda m: m["timestamp"])
        events = []

        events.extend(RelationshipEventEngine._detect_reply_patterns(sorted_msgs))
        events.extend(RelationshipEventEngine._detect_content_patterns(sorted_msgs))
        events.extend(RelationshipEventEngine._detect_time_patterns(sorted_msgs))
        events.extend(RelationshipEventEngine._detect_media_patterns(sorted_msgs))
        events.extend(RelationshipEventEngine._detect_conversation_flow(sorted_msgs))

        return events

    @staticmethod
    def _detect_reply_patterns(messages: list[dict]) -> list[dict]:
        events = []
        senders = set(m["sender"] for m in messages)

        for i in range(1, len(messages)):
            prev = messages[i - 1]
            curr = messages[i]
            if prev["sender"] == curr["sender"]:
                continue

            try:
                prev_ts = datetime.fromisoformat(prev["timestamp"])
                curr_ts = datetime.fromisoformat(curr["timestamp"])
                gap = (curr_ts - prev_ts).total_seconds()

                if gap < 60:
                    events.append({
                        "event_type": "instant_reply",
                        "weight": EVENT_DEFINITIONS["instant_reply"]["weight"],
                        "description": EVENT_DEFINITIONS["instant_reply"]["description"],
                        "occurred_at": curr["timestamp"],
                        "metadata": {"gap_seconds": gap},
                    })
            except (ValueError, KeyError):
                continue

        return events

    @staticmethod
    def _detect_content_patterns(messages: list[dict]) -> list[dict]:
        events = []
        from collections import Counter

        window_size = 5
        for i in range(len(messages)):
            msg = messages[i]
            content = msg.get("content", "").strip()

            if len(content) > 100:
                events.append({
                    "event_type": "long_text",
                    "weight": EVENT_DEFINITIONS["long_text"]["weight"],
                    "description": EVENT_DEFINITIONS["long_text"]["description"],
                    "occurred_at": msg["timestamp"],
                    "metadata": {"length": len(content)},
                })

            if any(w in content for w in ["晚安", "wanan", "早点休息", "睡了", "先睡了"]):
                events.append({
                    "event_type": "goodnight",
                    "weight": EVENT_DEFINITIONS["goodnight"]["weight"],
                    "description": EVENT_DEFINITIONS["goodnight"]["description"],
                    "occurred_at": msg["timestamp"],
                })

            if any(w in content for w in ["早安", "早上好", "早啊", "起床了"]):
                events.append({
                    "event_type": "morning_greeting",
                    "weight": EVENT_DEFINITIONS["morning_greeting"]["weight"],
                    "description": EVENT_DEFINITIONS["morning_greeting"]["description"],
                    "occurred_at": msg["timestamp"],
                })

            if "?" in content or "？" in content or any(q in content for q in ["吗", "呢", "怎么样", "如何"]):
                events.append({
                    "event_type": "question_asked",
                    "weight": EVENT_DEFINITIONS["question_asked"]["weight"],
                    "description": EVENT_DEFINITIONS["question_asked"]["description"],
                    "occurred_at": msg["timestamp"],
                })

            if i >= window_size:
                window = messages[i - window_size + 1:i + 1]
                short_replies = sum(
                    1 for m in window
                    if len(m.get("content", "").strip()) <= 3
                    and m["sender"] == msg["sender"]
                )
                if short_replies >= 3:
                    events.append({
                        "event_type": "cold_replies",
                        "weight": EVENT_DEFINITIONS["cold_replies"]["weight"],
                        "description": EVENT_DEFINITIONS["cold_replies"]["description"],
                        "occurred_at": msg["timestamp"],
                    })

        return events

    @staticmethod
    def _detect_time_patterns(messages: list[dict]) -> list[dict]:
        events = []

        for msg in messages:
            try:
                ts = datetime.fromisoformat(msg["timestamp"])
                hour = ts.hour

                if 0 <= hour < 5:
                    events.append({
                        "event_type": "late_night_interaction",
                        "weight": EVENT_DEFINITIONS["late_night_interaction"]["weight"],
                        "description": EVENT_DEFINITIONS["late_night_interaction"]["description"],
                        "occurred_at": msg["timestamp"],
                        "metadata": {"hour": hour},
                    })
            except (ValueError, KeyError):
                continue

        return events

    @staticmethod
    def _detect_media_patterns(messages: list[dict]) -> list[dict]:
        events = []

        for msg in messages:
            msg_type = msg.get("type", "text")

            if msg_type == MessageType.IMAGE.value:
                events.append({
                    "event_type": "image_share",
                    "weight": EVENT_DEFINITIONS["image_share"]["weight"],
                    "description": EVENT_DEFINITIONS["image_share"]["description"],
                    "occurred_at": msg["timestamp"],
                })

            if msg_type == MessageType.VIDEO_CALL.value:
                events.append({
                    "event_type": "video_call",
                    "weight": EVENT_DEFINITIONS["video_call"]["weight"],
                    "description": EVENT_DEFINITIONS["video_call"]["description"],
                    "occurred_at": msg["timestamp"],
                })

            if msg_type == MessageType.VOICE_CALL.value:
                try:
                    ts = datetime.fromisoformat(msg["timestamp"])
                    if 0 <= ts.hour < 5:
                        events.append({
                            "event_type": "late_night_voice",
                            "weight": EVENT_DEFINITIONS["late_night_voice"]["weight"],
                            "description": EVENT_DEFINITIONS["late_night_voice"]["description"],
                            "occurred_at": msg["timestamp"],
                        })
                except (ValueError, KeyError):
                    pass

        return events

    @staticmethod
    def _detect_conversation_flow(messages: list[dict]) -> list[dict]:
        events = []

        sender_msgs: dict[str, list[dict]] = {}
        for m in messages:
            s = m["sender"]
            if s not in sender_msgs:
                sender_msgs[s] = []
            sender_msgs[s].append(m)

        for sender, msgs in sender_msgs.items():
            for i in range(1, len(msgs)):
                try:
                    prev_ts = datetime.fromisoformat(msgs[i - 1]["timestamp"])
                    curr_ts = datetime.fromisoformat(msgs[i]["timestamp"])
                    gap = (curr_ts - prev_ts).total_seconds()

                    if gap > 6 * 3600:
                        prev_content = msgs[i - 1].get("content", "").strip()
                        if prev_content and len(prev_content) > 10:
                            events.append({
                                "event_type": "read_but_no_reply_long",
                                "weight": EVENT_DEFINITIONS["read_but_no_reply_long"]["weight"],
                                "description": EVENT_DEFINITIONS["read_but_no_reply_long"]["description"],
                                "occurred_at": msgs[i]["timestamp"],
                                "metadata": {"gap_hours": gap / 3600},
                            })
                except (ValueError, KeyError):
                    continue

        senders = list(sender_msgs.keys())
        if len(senders) >= 2:
            a, b = senders[0], senders[1]
            conversations = []
            current_conv = []
            for msg in messages:
                if msg["sender"] in (a, b):
                    current_conv.append(msg)
                else:
                    if current_conv:
                        conversations.append(current_conv)
                        current_conv = []
            if current_conv:
                conversations.append(current_conv)

            for conv in conversations:
                if len(conv) >= 20:
                    events.append({
                        "event_type": "long_conversation",
                        "weight": EVENT_DEFINITIONS["long_conversation"]["weight"],
                        "description": EVENT_DEFINITIONS["long_conversation"]["description"],
                        "occurred_at": conv[len(conv) // 2]["timestamp"],
                        "metadata": {"rounds": len(conv)},
                    })

                starters = {}
                for m in conv:
                    s = m["sender"]
                    try:
                        ts = datetime.fromisoformat(m["timestamp"])
                    except (ValueError, KeyError):
                        continue
                    date_key = ts.strftime("%Y-%m-%d")
                    if date_key not in starters:
                        starters[date_key] = s

                cold_start_count = 0
                for s in [a, b]:
                    starts = sum(1 for v in starters.values() if v == s)
                    cold_start_count += starts
                    if starts >= 1:
                        events.append({
                            "event_type": "start_new_topic",
                            "weight": EVENT_DEFINITIONS["start_new_topic"]["weight"],
                            "description": f"{EVENT_DEFINITIONS['start_new_topic']['description']} ({s})",
                            "occurred_at": conv[0]["timestamp"],
                            "metadata": {"starter": s, "count": starts},
                        })

        return events

    @staticmethod
    def compute_metrics(messages: list[dict], events: list[dict]) -> dict:
        """Compute aggregated metrics from messages and events."""
        if not messages:
            return {}

        total = len(messages)
        senders = list(set(m["sender"] for m in messages))
        sender_counts = {}
        for m in messages:
            s = m["sender"]
            sender_counts[s] = sender_counts.get(s, 0) + 1

        type_counts = {}
        for m in messages:
            t = m.get("type", "text")
            type_counts[t] = type_counts.get(t, 0) + 1

        avg_len = sum(len(m.get("content", "")) for m in messages) / max(total, 1)

        dates = []
        for m in messages:
            try:
                dates.append(datetime.fromisoformat(m["timestamp"]))
            except (ValueError, KeyError):
                pass

        date_range_days = 0
        if len(dates) >= 2:
            dates.sort()
            date_range_days = (dates[-1] - dates[0]).days or 1

        messages_per_day = total / max(date_range_days, 1)

        night_msgs = 0
        for m in messages:
            try:
                ts = datetime.fromisoformat(m["timestamp"])
                if 0 <= ts.hour < 5:
                    night_msgs += 1
            except (ValueError, KeyError):
                pass

        event_weights = sum(e.get("weight", 0) for e in events)

        event_type_counts = {}
        for e in events:
            et = e.get("event_type", "unknown")
            event_type_counts[et] = event_type_counts.get(et, 0) + 1

        image_count = type_counts.get(MessageType.IMAGE.value, 0)
        voice_count = type_counts.get(MessageType.VOICE_CALL.value, 0)
        video_count = type_counts.get(MessageType.VIDEO_CALL.value, 0)
        emoji_count = type_counts.get(MessageType.EMOJI.value, 0)

        response_gaps = []
        for i in range(1, len(messages)):
            if messages[i]["sender"] != messages[i - 1]["sender"]:
                try:
                    t1 = datetime.fromisoformat(messages[i - 1]["timestamp"])
                    t2 = datetime.fromisoformat(messages[i]["timestamp"])
                    response_gaps.append((t2 - t1).total_seconds() / 60)
                except (ValueError, KeyError):
                    pass

        avg_response_minutes = sum(response_gaps) / max(len(response_gaps), 1) if response_gaps else 0

        weekly_trend = []
        if dates:
            dates.sort()
            start = dates[0]
            end = dates[-1]
            current = start
            while current <= end:
                week_end = current + timedelta(days=7)
                week_count = sum(1 for d in dates if current <= d < week_end)
                weekly_trend.append({
                    "week_start": current.strftime("%Y-%m-%d"),
                    "message_count": week_count,
                })
                current = week_end

        return {
            "total_messages": total,
            "participants": senders,
            "sender_message_counts": sender_counts,
            "date_range_days": date_range_days,
            "messages_per_day": round(messages_per_day, 2),
            "avg_message_length": round(avg_len, 1),
            "night_interaction_ratio": round(night_msgs / max(total, 1), 3),
            "event_score_total": event_weights,
            "event_counts": event_type_counts,
            "image_count": image_count,
            "voice_count": voice_count,
            "video_count": video_count,
            "emoji_count": emoji_count,
            "avg_response_minutes": round(avg_response_minutes, 1),
            "weekly_trend": weekly_trend,
            "non_text_ratio": round((image_count + voice_count + video_count) / max(total, 1), 3),
        }
