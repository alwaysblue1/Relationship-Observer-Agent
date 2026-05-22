"""Enrich pattern cards with real utterance examples from EmpatheticDialogues.

Purpose (as specified by user):
    1. Expand pattern signals with real conversational data
    2. Enrich real emotional expressions for relationship semantic understanding
    3. NOT for model training — for deepening the pattern library

Approach:
    Match utterances to pattern cards based on linguistic signal profiles,
    not just emotional context labels. Each pattern card's signals[] describe
    the kinds of utterances that exemplify it.

Usage:
    cd backend
    python -m scripts.enrich_with_empathetic_dialogues
"""

import csv
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

# --- Signal → utterance extractors ---
# Each extractor takes an utterance string and returns a score 0-1
# indicating how well it matches that signal type.

SHORT_THRESHOLD = 15       # chars: "short message"
VERY_SHORT_THRESHOLD = 6   # chars: "cold/perfunctory reply"
LONG_THRESHOLD = 100       # chars: "long text"


def match_cold_reply(text: str) -> float:
    """Very short, dismissive, minimal engagement."""
    t = text.strip()
    if len(t) <= VERY_SHORT_THRESHOLD:
        return 0.95
    cold_words = ["whatever", "fine", "sure", "ok", "k", "nah", "meh", "nope",
                  "idk", "idc", "tbh", "maybe", "nothing", "alright",
                  "随便", "都行", "再说", "无所谓", "算了", "没什么", "没事",
                  "嗯", "哦", "啊", "额", "好", "行",
                  "你决定", "看着办", "不用了", "就这样"]
    lowered = t.lower()
    if any(w in lowered for w in cold_words) and len(t) <= 20:
        return 0.7
    if len(t) <= SHORT_THRESHOLD and not ("?" in t or "！" in t or "!" in t):
        return 0.5
    return 0.0


def match_emotional_disclosure(text: str) -> float:
    """Self-disclosure: feelings, personal experiences, vulnerability."""
    t = text.strip()
    if len(t) < 30:
        return 0.0
    disclosure_words = [
        "i feel", "i felt", "i've been feeling", "i am feeling",
        "i was so", "i'm so", "i just", "it hurts", "i cry", "i cried",
        "i worry", "i fear", "i struggle", "i wish", "i hope",
        "makes me feel", "makes me sad", "makes me happy",
        "i don't know what to do", "i can't stop thinking",
        "我觉得", "我感觉", "我很难", "我好想", "我真的很",
        "不知道怎么办", "心里", "难过", "害怕", "担心",
    ]
    lowered = t.lower()
    matches = sum(1 for w in disclosure_words if w in lowered)
    if matches >= 2:
        return 0.9
    if matches >= 1:
        return 0.6
    # Long first-person narrative
    if len(t) > 80 and lowered.count("i ") >= 4:
        return 0.5
    return 0.0


def match_repair_gesture(text: str) -> float:
    """Apologies, reconciliation attempts, olive branches."""
    t = text.strip().lower()
    repair_words = [
        "sorry", "apologize", "my bad", "i was wrong", "forgive",
        "i shouldn't have", "i didn't mean", "are you okay", "are you mad",
        "can we talk", "i miss you", "i miss talking", "let's talk",
        "i hope you're okay", "i've been thinking about you",
        "对不起", "抱歉", "我错了", "原谅", "别生气",
        "还在生气吗", "我们谈谈", "我想你", "是我的错",
    ]
    matches = sum(1 for w in repair_words if w in t)
    if matches >= 1:
        return min(0.95, 0.5 + matches * 0.2)
    return 0.0


def match_question(text: str) -> float:
    """Questions — curiosity, interest in the other person."""
    t = text.strip()
    if "?" in t or "？" in t:
        base = 0.5
        question_words = ["what", "how", "why", "when", "where", "who",
                          "do you", "are you", "have you", "did you", "would you",
                          "什么", "怎么", "为什么", "哪里", "谁", "吗", "呢"]
        lowered = t.lower()
        q_matches = sum(1 for w in question_words if w in lowered)
        return min(0.95, base + q_matches * 0.15)
    return 0.0


def match_question_back(text: str) -> float:
    """Questions directed back at the speaker — conversational reciprocity."""
    t = text.strip().lower()
    reciprocity = ["what about you", "how about you", "and you", "yourself",
                   "你呢", "那你呢", "你怎么样", "你也"]
    if any(w in t for w in reciprocity):
        return 0.9
    if match_question(text) > 0.4 and any(w in t for w in ["you", "your", "你"]):
        return 0.5
    return 0.0


def match_short_message(text: str) -> float:
    """Brief, casual messages — quick check-ins."""
    t = text.strip()
    if len(t) <= SHORT_THRESHOLD:
        return 0.8
    return 0.0


def match_long_text(text: str) -> float:
    """Substantial messages — invested, detailed communication."""
    t = text.strip()
    if len(t) >= LONG_THRESHOLD:
        return min(0.95, 0.6 + (len(t) - LONG_THRESHOLD) / 200)
    return 0.0


def match_positive_emotion(text: str) -> float:
    """Excitement, joy, celebration, warmth."""
    t = text.strip().lower()
    positive_words = [
        "awesome", "amazing", "great", "wonderful", "love", "beautiful",
        "congratulations", "congrats", "so happy", "so excited", "yay",
        "best", "favorite", "thank you", "thanks", "grateful",
        "太棒了", "真好", "很开心", "喜欢", "爱", "谢谢", "恭喜",
        "太好了", "哈哈", "嘿嘿",
    ]
    matches = sum(1 for w in positive_words if w in t)
    if matches >= 2:
        return 0.9
    if matches >= 1:
        return 0.5
    # Exclamation marks + positive vibe
    if ("!" in t or "！" in t) and len(t) > 10:
        return 0.3
    return 0.0


def match_daily_routine(text: str) -> float:
    """Greetings, check-ins, daily rhythm markers."""
    t = text.strip().lower()
    routine_words = [
        "good morning", "morning", "goodnight", "good night", "晚安", "早安",
        "起床了", "早啊", "早上好", "睡了", "hello", "hi", "hey",
        "how was your day", "how are you", "how's it going",
        "今天怎么样", "在干嘛", "吃了吗", "到家了吗",
        "have a good day", "take care", "talk tomorrow",
    ]
    if any(w in t for w in routine_words):
        return 0.85
    return 0.0


def match_late_night(text: str) -> float:
    """Late-night style: reflective, confessional, emotionally raw."""
    t = text.strip().lower()
    night_words = [
        "can't sleep", "insomnia", "late", "midnight",
        "lying in bed", "thinking about", "overthinking",
        "睡不着", "失眠", "深夜", "凌晨", "半夜",
        "夜深了", "还在想",
    ]
    if any(w in t for w in night_words):
        return 0.8
    # Long reflective messages at night-like quality
    if len(t) > 80 and t.count("i ") >= 5:
        return 0.4
    return 0.0


def match_anger_frustration(text: str) -> float:
    """Anger, frustration, passive-aggression."""
    t = text.strip().lower()
    anger_words = [
        "angry", "mad", "furious", "pissed", "annoying", "frustrating",
        "hate", "stupid", "ridiculous", "whatever", "seriously",
        "you always", "you never", "i can't believe",
        "生气", "烦", "讨厌", "滚", "够了", "无语",
        "你总是", "你从来", "随便你", "爱咋咋地",
    ]
    matches = sum(1 for w in anger_words if w in t)
    if matches >= 1:
        return min(0.9, 0.4 + matches * 0.2)
    # ALL CAPS sections signal anger
    caps_ratio = sum(1 for c in t if c.isupper()) / max(len(t), 1)
    if caps_ratio > 0.3 and len(t) > 10:
        return 0.4
    return 0.0


def match_future_projection(text: str) -> float:
    """Future-oriented language: plans, "someday", "next time"."""
    t = text.strip().lower()
    future_words = [
        "someday", "one day", "next time", "in the future",
        "i will", "we will", "we should", "let's", "i plan",
        "i want to", "i hope to", "looking forward",
        "以后", "下次", "将来", "总有一天", "到时候",
        "我们一起去", "等...就", "改天",
    ]
    matches = sum(1 for w in future_words if w in t)
    if matches >= 1:
        return min(0.9, 0.5 + matches * 0.2)
    return 0.0


def match_third_party(text: str) -> float:
    """Mentions of third parties, comparisons, external social references."""
    t = text.strip().lower()
    third_words = [
        "my friend", "my mom", "my dad", "my boss", "my coworker",
        "my ex", "my partner", "my boyfriend", "my girlfriend",
        "my husband", "my wife", "they said", "he said", "she said",
        "我朋友", "我妈", "我爸", "同事", "前男友", "前女友",
        "别人", "他们说", "你看人家",
    ]
    if any(w in t for w in third_words):
        return 0.8
    return 0.0


def match_emoji_heavy(text: str) -> float:
    """Playful, emoji/sticker-heavy, informal tone."""
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF\U00002600-\U000026FF"
        "\U0000FE00-\U0000FEFF☀-⛿✀-➿]"
    )
    emoji_count = len(emoji_pattern.findall(text))
    # Also count common text emojis
    text_emoji = [":)", ":D", ":P", "XD", "lol", "haha", "hehe", "lmao",
                  "哈哈", "嘿嘿", "嘻嘻", "呵呵"]
    text_count = sum(1 for e in text_emoji if e in text.lower())
    total = emoji_count + text_count
    if total >= 3:
        return 0.9
    if total >= 1:
        return 0.5
    return 0.0


def match_defensive(text: str) -> float:
    """Defensive, justifying, pushing back."""
    t = text.strip().lower()
    defensive_words = [
        "i didn't", "i did not", "you misunderstood", "that's not what i",
        "you're wrong", "no i", "it's not my fault", "i never said",
        "我没有", "不是这样的", "你误会了", "不是我的问题",
        "你怎么这么说", "我不是那个意思",
    ]
    if any(w in t for w in defensive_words):
        return 0.8
    return 0.0


# --- Pattern card → signal extractor mapping ---
# Maps each pattern card's signal names to the extractor functions above.
# Each card gets scored against utterances using its signal extractors.

EXTRACTOR_MAP = {
    "cold_reply": match_cold_reply,
    "short_message": match_short_message,
    "long_text": match_long_text,
    "emotional_disclosure": match_emotional_disclosure,
    "question_asked": match_question,
    "question_back": match_question_back,
    "positive_event": match_positive_emotion,
    "repair_gesture": match_repair_gesture,
    "daily_rhythm": match_daily_routine,
    "late_night": match_late_night,
    "anger": match_anger_frustration,
    "future_projection": match_future_projection,
    "third_party": match_third_party,
    "emoji_heavy": match_emoji_heavy,
    "defensive": match_defensive,
    # Composite signal names from our card signals
    "cold_replies": match_cold_reply,
    "instant_reply": match_short_message,
    "rapid_reply": match_short_message,
    "emoji_bloom": match_emoji_heavy,
    "long_conversation": match_long_text,
    "question_surge": match_question,
    "inside_joke_dense": match_emoji_heavy,
    "media_shared": match_positive_emotion,
    "passive_aggression": match_anger_frustration,
    "stonewall": match_cold_reply,
    "defensive_reply": match_defensive,
    "reply_expectation": match_question,
    "weekend_silence": match_cold_reply,
    "routine_disruption": match_cold_reply,
    "future_projection_declining": match_cold_reply,
    "we_narrative": match_emotional_disclosure,
    "conflict_acknowledged": match_repair_gesture,
    "conflict_escalation": match_anger_frustration,
    "resume_awkward": match_repair_gesture,
    "repair_gesture": match_repair_gesture,
    "third_party_mention": match_third_party,
    "initiative_gap_widening": match_question,
    "daily_rhythm_forming": match_daily_routine,
    "emoji_declining": match_cold_reply,
    "inside_joke_start": match_emoji_heavy,
    "nickname_usage": match_positive_emotion,
    "emotional_disclosure_declining": match_cold_reply,
    "question_surge_declining": match_cold_reply,
    "question_back_declining": match_cold_reply,
    "conversation_loop_closure": match_cold_reply,
    "instant_reply_declining": match_cold_reply,
    "weekly_msg_count_declining": match_cold_reply,
    "message_length_declining": match_cold_reply,
    "topic_shallowing": match_cold_reply,
    "deep_topic_declining": match_cold_reply,
    "start_new_topic": match_question,
    "contact_exchange": match_positive_emotion,
    "inside_joke_declining": match_cold_reply,
    "long_conversation_declining": match_cold_reply,
    "reply_delay_long": match_cold_reply,
    "reply_delay_slight": match_cold_reply,
    "reply_delay_comfortable": match_short_message,
    "reply_delay_volatile": match_short_message,
    "long_absence": match_cold_reply,
    "stable_rhythm": match_daily_routine,
    "balanced_turn_taking": match_question,
    "message_length_match": match_short_message,
    "reply_rhythm_sync": match_daily_routine,
    "no_anxiety_signal": match_positive_emotion,
    "selective_response": match_cold_reply,
    "formal_politeness": match_cold_reply,
    "formality_increase": match_cold_reply,
    "nickname_declining": match_cold_reply,
    "conflict_resolved": match_repair_gesture,
    "conflict_recurrence": match_anger_frustration,
    "misunderstanding_trigger": match_defensive,
    "availability_mismatch": match_cold_reply,
    "life_stage_mismatch": match_emotional_disclosure,
    "parallel_presence": match_short_message,
    "emoji_light": match_emoji_heavy,
    "resume_smooth": match_positive_emotion,
}


def score_utterance_for_card(utterance: str, card: dict) -> float:
    """Score how well an utterance exemplifies a pattern card's signals."""
    signals = card.get("signals", [])
    if not signals:
        return 0.0

    scores = []
    for sig in signals:
        extractor = EXTRACTOR_MAP.get(sig)
        if extractor:
            s = extractor(utterance)
            if s > 0:
                scores.append(s)

    if not scores:
        return 0.0
    # Weighted: best-matching signals contribute more
    scores.sort(reverse=True)
    return scores[0] * 0.6 + sum(scores[1:]) / max(len(scores), 1) * 0.4


# --- Emotional context → category mapping (for pre-filtering) ---
CONTEXT_TO_CATEGORY = {
    "lonely": "distancing", "disappointed": "distancing",
    "annoyed": "distancing", "disgusted": "distancing",
    "sad": "distancing", "devastated": "distancing",
    "embarrassed": "distancing", "ashamed": "distancing",
    "apprehensive": "distancing",
    "grateful": "harmony", "caring": "harmony", "trusting": "harmony",
    "faithful": "harmony", "content": "harmony", "joyful": "harmony",
    "excited": "emergence", "hopeful": "emergence",
    "confident": "emergence", "anticipating": "emergence",
    "impressed": "emergence", "sentimental": "emergence",
    "angry": "conflict_repair", "furious": "conflict_repair",
    "guilty": "conflict_repair", "afraid": "conflict_repair",
    "terrified": "conflict_repair", "anxious": "conflict_repair",
    "jealous": "asymmetric", "proud": "asymmetric",
    "nostalgic": "asymmetric",
    "surprised": "temporal", "prepared": "temporal",
}


def load_dataset(data_dir: str) -> list[dict]:
    rows = []
    for split in ["train.csv", "valid.csv", "test.csv"]:
        path = Path(data_dir) / split
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                utt = row.get("utterance", "")
                # Filter malformed rows where CSV parsing failed
                if "conv_id" in utt or len(utt) > 2000 or utt.count(",") > 30:
                    continue
                if not utt or len(utt.strip()) < 2:
                    continue
                rows.append(row)
    return rows


def enrich():
    data_dir = Path(__file__).resolve().parent.parent.parent / "empatheticdialogues"
    cards_path = Path(__file__).resolve().parent.parent / "app" / "data" / "pattern_cards.json"

    if not data_dir.exists():
        print(f"Dataset not found at {data_dir}")
        print("Download from: https://dl.fbaipublicfiles.com/parlai/empatheticdialogues/empatheticdialogues.tar.gz")
        sys.exit(1)

    print("Loading EmpatheticDialogues ...")
    rows = load_dataset(str(data_dir))
    print(f"Loaded {len(rows)} utterances")

    # Pre-group utterances by category for efficient scoring
    cat_rows: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        raw = row["utterance"].replace("_comma_", ",").strip()
        if not raw or len(raw) < 2:
            continue
        context = row["context"]
        category = CONTEXT_TO_CATEGORY.get(context)
        if category:
            cat_rows[category].append({"utterance": raw, "context": context})

    for cat in ["emergence", "harmony", "distancing", "conflict_repair", "asymmetric", "temporal"]:
        print(f"  {cat}: {len(cat_rows.get(cat, []))} utterances")

    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)
    print(f"\nLoaded {len(cards)} pattern cards")

    # For each card, score utterances from matching category and pick top matches
    enriched = 0
    for i, card in enumerate(cards):
        cat = card["category"]
        pool = cat_rows.get(cat, [])
        if not pool:
            continue

        # Score all utterances in the pool against this card
        scored = []
        # Sample pool if too large (20k max per card)
        sample_pool = random.sample(pool, min(20000, len(pool)))
        for item in sample_pool:
            score = score_utterance_for_card(item["utterance"], card)
            if score > 0.3:  # minimum relevance threshold
                scored.append((score, item["utterance"]))

        scored.sort(key=lambda x: x[0], reverse=True)

        # Pick distinct top examples
        seen = set()
        examples = []
        for s, utt in scored:
            key = utt.lower().strip().rstrip(".!?。！？")
            if key not in seen and len(utt) >= 3:
                seen.add(key)
                examples.append(utt)
            if len(examples) >= 15:
                break

        if examples:
            card["utterance_examples"] = examples
            enriched += 1

        if (i + 1) % 25 == 0:
            print(f"  Processed {i+1}/{len(cards)} cards ...")

    print(f"\nEnriched {enriched}/{len(cards)} cards with utterance examples")

    # Write back
    with open(cards_path, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    print(f"Written to {cards_path}")

    # Show quality samples
    print("\n=== Sample quality verification ===")
    for card in random.sample(cards, 8):
        examples = card.get("utterance_examples", [])
        if examples:
            print(f"\n[{card['category']}] {card['pattern_name']}")
            print(f"  Description: {card['description']}")
            print(f"  Example utterances:")
            for ex in examples[:4]:
                print(f'    → "{ex}"')


if __name__ == "__main__":
    enrich()
