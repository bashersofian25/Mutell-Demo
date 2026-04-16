#!/usr/bin/env python3
"""
POS Monitoring — Single load test script.

1. Generates 120 conversation sample files (6 categories × 20 each)
2. Sends them in batches of 3 (one per terminal) every 3 minutes
3. Cycles through all conversations and repeats

Usage:  python3 run_load_test.py
Stop:   Ctrl+C
"""

import asyncio
import json
import random
import re
from datetime import datetime, timedelta, UTC
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000/api/v1"
INTERVAL_SECONDS = 10  # 3 minutes between batches

TERMINALS = [
    ("pk_live_z_keE5DCS0bRHAD37RtUtkw_M94CnfHlBKABxU0cohs", "POS-01"),
    ("pk_live_pUTETgveVH1qsTxomIuyNfTJY5IQi3bD4qoMhsH8hSM", "POS-02"),
    ("pk_live_l4TndFa8PMv5c66WjXdTBEgFFO6FQwJyOBFxrnScmkI", "POS-03"),
]

CONVERSATIONS_DIR = Path(__file__).parent / "samples" / "conversations"

# ── Generation: STT helpers ──────────────────────────────────────────────────

FILLER_WORDS = ["um", "uh", "like", "you know", "I mean", "actually", "basically"]
STT_ERRORS = {
    "the": "teh", "and": "adn", "you": "u", "your": "ur",
    "to": "2", "for": "4", "are": "r", "too": "to",
    "there": "their", "their": "there", "its": "it's",
}


def apply_stt_transformations(text, confidence=0.9, audio_quality="good"):
    if confidence < 0.9 and random.random() < 0.3:
        text = text.replace(" ", f" {random.choice(FILLER_WORDS)} ", 1)
    if confidence < 0.85 and random.random() < 0.2:
        words = text.split()
        if words:
            text = text.replace(" ", f" {words[0]} ", 1)
    if confidence < 0.8:
        for original, error in STT_ERRORS.items():
            if random.random() < 0.1:
                text = text.replace(original, error)
    if audio_quality == "poor" and random.random() < 0.3:
        text = text.replace(".", "")
    if audio_quality == "poor" and random.random() < 0.1:
        text = f"{text[:len(text)//2]} [inaudible] {text[len(text)//2:]}"
    return text


# ── Generation: conversation builders ────────────────────────────────────────

def _conv(idx, base_time, category, desc, metadata, lines):
    return {
        "id": f"{category}_{idx+1}",
        "category": category,
        "description": desc,
        "duration_minutes": 5,
        "started_at": base_time.isoformat(),
        "ended_at": (base_time + timedelta(minutes=5)).isoformat(),
        "metadata": metadata,
        "raw_text": "\n".join(lines),
    }


def _meta(index, **overrides):
    defaults = {
        "store_location": ["عمان", "إربد", "الزرقاء"][index % 3],
        "agent_name": ["أحمد", "فاطمة", "محمد"][index % 3],
        "customer_type": "regular",
        "language": "ar_JO",
        "format": "stt",
        "confidence": [0.85, 0.92, 0.78][index % 3],
        "audio_quality": ["good", "average", "poor"][index % 3],
    }
    defaults.update(overrides)
    return defaults


# ── Generation: per-category generators ──────────────────────────────────────

def gen_arabic(i, t):
    lines = [
        ["العميل: شو هذا المنتج اللي عنكم؟ منيح شو؟ بس يلقاوه معطوب!",
         "الموظف: آسف يا سيدي، شو المشكلة بالضبط؟",
         "العميل: شو المشكلة؟ المنتج ما يشتغل من أصله! OK؟",
         "الموظف: خليني أشوفلك بدل منو، جاري هنالك الأمر.",
         "العميل: God Damn it! انتظرت ساعات!",
         "الموظف: آسف يا سيدي، هنالك شلون؟"],
        ["العميل: هذا product مش منيح الجودة! materials رديئة!",
         "الموظف: آسف لسماع ذلك. What's the issue exactly?",
         "العميل: واللي بالداخل رخيص بس الظاهر good!",
         "الموظف: Okay، هل بدك exchange أو refund؟",
         "العميل: Refund بدك! بس اللي عندكم مش منيح!",
         "الموظف: Yes، سأحل المشكلة من وراك."],
        ["العميل: يلا بدك discount؟ السعر عالي بعض الشيء.",
         "الموظف: Well، للأسف السعر fixed مش قابل للتغيير.",
         "العميل: شو هالمفهوم؟ أنا customer من زمان عندكم!",
         "الموظف: I understand، بس policy ما بدي تغيير.",
         "العميل: ههه OK. إذن شغلة تانية، free delivery؟",
         "الموظف: Yes، هنالك free delivery إذا فوق 100 دينار."],
        ["العميل: Hello، عندي problem مع order رقم 456.",
         "الموظف: Welcome يا عم! شو الموضوع؟",
         "العميل: Product ما وصل لحد الآن. It's been 4 days!",
         "الموظف: Okay، خليني أشوف tracking للشحن.",
         "العميل: Thanks يا باشa. هون service OK.",
         "الموظف: You're welcome. أي حاجة ثانية بخدمتك."],
    ]
    return _conv(i, t, "arabic_only",
                 "Jordanian customer service conversation with minimal English",
                 _meta(i, english_percentage=[0.05, 0.03, 0.02][i % 3],
                       has_profanity=i > 15,
                       tone=["غاضب", "لطيف", "مربك", "عاجز"][i % 4]),
                 lines[i % len(lines)])


def gen_mixed(i, t):
    lines_set = [
        ["Customer: Hello, I need help yaani.",
         "Agent: Welcome! How can I help you, ya habibi?",
         "Customer: I'm looking for phone, Jordanian style.",
         "Agent: Yes, we have nice phones. What's your budget?",
         "Customer: Around 500 dinar, shwaya expensive.",
         "Agent: Perfect! We have iPhone for this price."],
        ["Customer: Excuse me, I have problem with my order.",
         "Agent: Welcome sir, welcome. What's the issue?",
         "Customer: The shipping is too slow, walla!",
         "Agent: I understand, sir. Give me 2 minutes.",
         "Customer: OK, but make it fast, yaani.",
         "Agent: Yes, sir, thank you for your patience."],
    ]
    return _conv(i, t, "mixed_language",
                 "Mixed Jordanian Arabic/English conversation",
                 _meta(i, language="mixed_JO",
                       customer_type=["tourist", "expat", "local"][i % 3],
                       english_percentage=[0.4, 0.5, 0.6][i % 3]),
                 lines_set[i % len(lines_set)])


def gen_impolite(i, t):
    lines_set = [
        ["العميل: شو هذا؟ service عندكم sucks!",
         "الموظف: آسف يا سيدي، شو المشكلة؟",
         "العميل: المشكلة أنكم بطئون! God Damn it!",
         "الموظف: آسف، خليني أحل المشكلة من وراك.",
         "العميل: ما في عندي time! This is unacceptable!",
         "الموظف: Yes، سأحلها فوراً."],
        ["العميل: أود أن أبلغ عن سوء الخدمة في متجركم!",
         "الموظف: آسف لسماع ذلك. كيف يمكنني مساعدتك؟",
         "العميل: الخدمة لديكم سيئة جداً! Very bad service!",
         "الموظف: أفهم قلقكم. سأقدم شكواكم.",
         "العميل: أريد إجراء فوري وcompensation!",
         "الموظف: Yes، سأحول الأمر للإدارة."],
        ["العميل: ما بدعوتكم! ليش ما تعملون شي؟!",
         "الموظف: آسف يا سيدي، رجاءً هدوء.",
         "العميل: HELL NO! أنا مش هدأ! This is bullshit!",
         "الموظف: رجاءً، اذكر لي المشكلة لأساعدك.",
         "العميل: أنا راح أشتكي عليكم everywhere!",
         "الموظف: Okay، Manager راح يتواصل معك."],
    ]
    return _conv(i, t, "impolite",
                 "Impolite Jordanian conversation with challenging behavior",
                 _meta(i, customer_type="challenging",
                       has_profanity=True,
                       threat_level=["low", "medium", "high"][i % 3],
                       tone=["عادي", "رسمي", "عدواني"][i % 3]),
                 lines_set[i % len(lines_set)])


def gen_unknown(i, t):
    lines_set = [
        ["العميل: يلا في product من اليونان؟",
         "الموظف: آسف، بس عندينا products من دول عربية.",
         "العميل: شو؟ مافي شيء من اليونان؟ Seriously?",
         "الموظف: للأسف، نعم. عندينا بدل منه products سورية.",
         "العميل: This is not what I want!",
         "الموظف: آسف يا سيدي، ممكن شي آخر؟"],
        ["العميل: Hello، هل عندكوا phones جديدة جداً؟ Like iPhone 15?",
         "الموظف: Welcome! نعم، عندينا iPhone 14 بس.",
         "العميل: بس 15؟ This is old school!",
         "الموظف: للأسف، 15 not available بعد في الأردن.",
         "العميل: How? هذا Impossible!",
         "الموظف: Yes، بس 14 ممتاز، وعمل Jordanian warranty."],
    ]
    return _conv(i, t, "unknown_items",
                 "Customer asking for unavailable items",
                 _meta(i, customer_type="confused", item_exists=False),
                 lines_set[i % len(lines_set)])


def gen_sst(i, t):
    text_lines = [
        "مرحباً يا أحمد، عندي problem مع product",
        "Welcome يا عم! شو المشكلة؟",
        "product ما يعمل من أول ما اشتريته",
        "آسف، شو فيه بالضبط؟",
        "يلا يعني machine مش شغالة",
        "خليني أشوف لك بدل منه",
        "OK بس ده يفضل في Warranty؟",
        "Yes، Warranty سنتين كاملة",
        "walla؟ thank you يا أحمد",
    ]
    conv = _conv(i, t, "sst_format",
                 "Speech-to-Text formatted Jordanian conversation",
                 _meta(i), text_lines)
    conv["metadata"]["word_count"] = len(" ".join(text_lines).split())
    return conv


def gen_edge(i, t):
    lines_set = [
        ["العميل: مرحباً", "الموظف: مرحباً", "العميل: باي"],
        ["العميل: يا أخي، عندي لك مشكلة كبيرة جداً أنا شفت منتج في موقعكم",
         "الموظف: أهلاً يا عم، كيف يمكنني مساعدتك اليوم؟",
         "العميل: يا أخي، أنا بيشتري product وأريد service ممتاز",
         "الموظف: طبعاً يا عم، نحن خدمتنا ممتازة جداً",
         "العميل: الله يعلم فيكم، أنا عميل من زمان",
         "الموظف: نشكرك يا عم على ثقتكم بنا",
         "العميل: walla thank you جداً"],
        ["العميل: ...", "الموظف: آلو؟ في أحد؟",
         "العميل: ...", "الموظف: يا سيدي؟",
         "العميل: نعم", "الموظف: كيف يمكنني مساعدتك؟",
         "العميل: ..."],
        ["العميل: يا جماعة، عندي سؤال... شو هذا... product... walla؟",
         "الموظف: آسف، كيف يمكنني أساعدك يا سيدي؟",
         "العميل: يعني أريد... product من جودة جيدة... بس price؟",
         "الموظف: عندي العديد products جودة ممتازة",
         "العميل: OK شوف انت، أي product منيح؟"],
    ]
    return _conv(i, t, "edge_cases",
                 "Edge case conversation scenario",
                 _meta(i,
                       customer_type=["confused", "silent", "rambling"][i % 3],
                       edge_case_type=["short", "long", "empty", "confused"][i % 4]),
                 lines_set[i % len(lines_set)])


GENERATORS = {
    "arabic_only":    gen_arabic,
    "mixed_language": gen_mixed,
    "impolite":       gen_impolite,
    "unknown_items":  gen_unknown,
    "sst_format":     gen_sst,
    "edge_cases":     gen_edge,
}


# ── Step 1: Generate all conversation files ──────────────────────────────────

def generate_conversations():
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    base_time = datetime(2024, 1, 15, 9, 0, tzinfo=UTC)
    count = 0

    for category, gen in GENERATORS.items():
        for i in range(20):
            conv = gen(i, base_time + timedelta(minutes=i * 3))

            if conv["metadata"].get("format") == "stt":
                conf = conv["metadata"]["confidence"]
                quality = conv["metadata"]["audio_quality"]
                conv["raw_text"] = apply_stt_transformations(conv["raw_text"], conf, quality)

            filename = f"conv_{i+1:03d}_{category.replace('_', '-')}.json"
            with open(CONVERSATIONS_DIR / filename, "w", encoding="utf-8") as f:
                json.dump(conv, f, ensure_ascii=False, indent=2)
            count += 1

    print(f"Generated {count} conversation files in {CONVERSATIONS_DIR}")
    return count


# ── Step 2: Send loop ────────────────────────────────────────────────────────

def clean_transcript(text):
    text = re.sub(r'(العميل|الموظف|Customer|Agent):?\s*', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def load_conversation_files():
    files = sorted(CONVERSATIONS_DIR.glob("conv_*.json"))
    conversations = []
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["raw_text"] = clean_transcript(data.get("raw_text", ""))
        data["word_count"] = len(data["raw_text"].split())
        conversations.append(data)
    return conversations


async def send_one(client, api_key, terminal_name, conv):
    now = datetime.now(UTC)
    started = now - timedelta(minutes=5)
    ended = now - timedelta(minutes=1)

    payload = {
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "raw_text": conv["raw_text"],
        "word_count": conv["word_count"],
    }

    try:
        resp = await client.post(
            f"{API_BASE}/slots",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        ok = resp.status_code in (200, 201)
        tag = "ok" if ok else f"ERR {resp.status_code}"
        print(f"  [{terminal_name}] {conv['id']} ({conv['category']}) — {tag}")
        return ok
    except Exception as e:
        print(f"  [{terminal_name}] {conv['id']} — ERROR: {e}")
        return False


async def send_loop():
    conversations = load_conversation_files()
    if not conversations:
        print("No conversation files found!")
        return

    num_terminals = len(TERMINALS)
    total = len(conversations)
    batches_per_cycle = total // num_terminals

    print(f"\nLoaded {total} conversations")
    print(f"Terminals: {', '.join(name for _, name in TERMINALS)}")
    print(f"Batches per cycle: {batches_per_cycle} ({batches_per_cycle * INTERVAL_SECONDS // 60} min)")
    print(f"API: {API_BASE}\n")

    total_req = 0
    total_ok = 0
    idx = 0

    try:
        import httpx
    except ImportError:
        print("httpx is required. Install it with:  pip install httpx")
        return

    try:
        batch_num = 1
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[Batch {batch_num}] {ts} — sending {num_terminals} requests")

                tasks = []
                for api_key, name in TERMINALS:
                    conv = conversations[idx % total]
                    tasks.append(send_one(client, api_key, name, conv))
                    idx += 1

                results = await asyncio.gather(*tasks)
                ok_count = sum(1 for r in results if r is True)
                total_req += num_terminals
                total_ok += ok_count

                rate = (total_ok / total_req * 100) if total_req else 0
                print(f"  Batch result: {ok_count}/{num_terminals} ok  |  "
                      f"Overall: {total_ok}/{total_req} ({rate:.1f}%)\n")

                if idx >= total:
                    print(f"  *** Full cycle complete — restarting from file 0 ***\n")
                    idx = 0

                batch_num += 1
                print(f"  Next batch in {INTERVAL_SECONDS // 60} minutes...")
                await asyncio.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        pct = f"({total_ok / total_req * 100:.1f}%)" if total_req else ""
        print(f"\n\nStopped. {total_ok}/{total_req} successful {pct}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  POS Monitoring — Load Test")
    print("=" * 60)

    print("\nStep 1: Generating conversations...")
    count = generate_conversations()
    if count == 0:
        print("No conversations generated. Aborting.")
        return

    print("\nStep 2: Starting send loop (Ctrl+C to stop)...")
    asyncio.run(send_loop())


if __name__ == "__main__":
    main()
