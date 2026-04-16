#!/usr/bin/env python3
"""Send 100 STT-style slot requests per terminal via curl subprocess."""
import json
import random
import subprocess
import sys
from datetime import UTC, datetime, timedelta

API = "http://localhost:8000/api/v1/slots"
TERMINALS = [
    ("pk_live_A7gDMaq-UPCc4Ubmz9fYKY6qQAHvg42xQ34bDlwgaS0", "POS-01"),
    ("pk_live_cRQDNPo_z04kOQ4M5_N8fPcwJ5BRa9PEGzVHvd7NlrU", "POS-02"),
    ("pk_live_8JOpSWhsUvVZNCv50ihZ6azdVuvEoEpjRENB_32h26A", "POS-03"),
]

PRODUCTS = [
    "sugar", "flour", "rice", "cooking oil", "milk", "bread", "eggs", "butter",
    "tomatoes", "onions", "potatoes", "bananas", "apples", "chicken breast",
    "beef mince", "pasta", "soap", "toothpaste", "detergent", "tissue paper",
    "bottled water", "soft drink", "coffee", "tea bags", "cornflakes",
    "salt", "pepper", "garlic", "ginger", "carrots", "cabbage",
    "bell peppers", "cucumber", "lettuce", "oranges", "grapes",
    "yogurt", "cheese", "margarine", "jam", "honey",
    "biscuits", "chocolate", "chips", "groundnuts", "juice",
    "canned beans", "canned tomatoes", "ketchup", "mayonnaise", "mustard",
]

GREETINGS = [
    "good morning welcome to our store",
    "hello hi good afternoon",
    "good evening welcome",
    "hi there how can i help you today",
    "welcome to quick mart",
    "morning please come in",
    "hello thanks for stopping by",
    "hi welcome how are you doing today",
    "good morning sir please",
    "afternoon madam what can i get for you",
]

ISSUES = [
    "the price on the shelf was different from what you just charged",
    "i bought this same item last week for less",
    "the expiry date on this bread is tomorrow can i get a fresh one",
    "you gave me the wrong change i gave you five thousand",
    "i asked for two of these not one",
    "this milk is leaking can you check another one",
    "the promotion says buy two get one free but its not reflecting",
    "the card reader declined my card but i have money in my account",
    "can i return this i bought it yesterday and its defective",
    "do you have a loyalty card program",
]

CLOSINGS = [
    "thank you very much have a nice day",
    "thanks for shopping with us please come again",
    "your receipt is here thank you madam",
    "bye bye see you next time",
    "thanks you have a blessed day",
    "thank you sir enjoy your evening",
    "please come back again we appreciate your business",
    "thanks take care goodbye",
    "have a good one thank you for coming",
    "bye now have a wonderful day ahead",
]

ARTIFACTS = [
    "um", "uh", "ah", "mm", "so", "like", "you know", "i mean",
    "basically", "actually", "right", "okay so", "let me see",
    "just a moment", "one second please", "hold on",
]

FILLERS = [
    "[noise]", "[clears throat]", "[pause]", "[background chatter]",
    "[coins jingling]", "[beep]", "[receipt printing]",
]

MISPRON = {
    "cooking oil": ["cooking all", "cooking oel"],
    "toothpaste": ["tooth paste", "two paste"],
    "tissue paper": ["issue paper", "tishu paper"],
    "chicken breast": ["chicken brest"],
    "cornflakes": ["corn flakes"],
    "bottled water": ["bottle water", "bottled wata"],
    "soft drink": ["sot drink"],
    "groundnuts": ["ground nuts", "grand nuts"],
    "cabbage": ["cabbege"],
    "cucumber": ["cucumba"],
    "ketchup": ["catchup"],
    "mayonnaise": ["mayonaise"],
    "yogurt": ["yoghurt"],
}

ITEM_PATTERNS = [
    "i need {p} please",
    "can i get one {p}",
    "give me {p}",
    "let me have two {p}",
    "do you have {p}",
    "i will take {p} and",
    "add {p} for me",
    "{p} how much is that",
    "one {p} please",
    "i want to buy {p}",
]


def gen_transcript():
    n = random.randint(2, 8)
    items = random.sample(PRODUCTS, min(n, len(PRODUCTS)))
    lines = [random.choice(GREETINGS)]

    if random.random() < 0.15:
        lines.append(random.choice(FILLERS))

    for item in items:
        if random.random() < 0.2:
            lines.append(random.choice(ARTIFACTS))
        if random.random() < 0.3 and item in MISPRON:
            spoken = random.choice(MISPRON[item])
        else:
            spoken = item
        lines.append(random.choice(ITEM_PATTERNS).format(p=spoken))

    if random.random() < 0.25:
        lines.append(random.choice(ISSUES))
    if random.random() < 0.2:
        lines.append(random.choice(ARTIFACTS))

    lines.append("okay let me total that for you")
    if random.random() < 0.1:
        lines.append("[receipt printing]")

    amt = random.randint(500, 25000)
    lines.append(random.choice([
        f"that will be {amt} shillings",
        f"your total is {amt} please",
        f"that comes to {amt} shillings sir",
        f"the total is {amt} madam",
    ]))

    lines.append(random.choice([
        "here is my card", "i will pay with mobile money",
        "cash here you go", "let me use mpesa",
        "i have the exact amount in cash", "card please",
    ]))

    if random.random() < 0.15:
        lines.append(random.choice(ARTIFACTS))

    lines.append("payment received thank you")
    lines.append(random.choice(CLOSINGS))
    return " ".join(lines)


def send_slot(api_key, idx, name):
    now = datetime.now(UTC)
    started = now - timedelta(minutes=random.randint(2, 300))
    ended = started + timedelta(seconds=random.randint(30, 600))
    text = gen_transcript()
    payload = json.dumps({
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "raw_text": text,
        "word_count": len(text.split()),
    })

    result = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
         "-X", "POST", API,
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {api_key}",
         "-d", payload],
        capture_output=True, text=True, timeout=30,
    )
    code = int(result.stdout.strip()) if result.stdout.strip() else 0
    if code in (200, 201, 202):
        return "ok"
    return f"ERR {code}"


def main():
    ok = 0
    fail = 0
    total = 100 * len(TERMINALS)
    print(f"Sending {total} slots ({len(TERMINALS)} terminals x 100)")
    print()

    for api_key, name in TERMINALS:
        print(f"--- {name} ---")
        for i in range(100):
            status = send_slot(api_key, i, name)
            if status == "ok":
                ok += 1
            else:
                fail += 1
                print(f"  #{i+1:03d} {status}")
        print(f"  {name} done")
        print()

    print(f"Results: {ok} succeeded, {fail} failed out of {total}")


if __name__ == "__main__":
    main()
