#!/usr/bin/env bash
# Load test: 100 slots per terminal via curl
# Usage: bash scripts/load_test.sh

API="http://localhost:8000/api/v1/slots"
KEYS=("pk_live_A7gDMaq-UPCc4Ubmz9fYKY6qQAHvg42xQ34bDlwgaS0"
      "pk_live_cRQDNPo_z04kOQ4M5_N8fPcwJ5BRa9PEGzVHvd7NlrU"
      "pk_live_8JOpSWhsUvVZNCv50ihZ6azdVuvEoEpjRENB_32h26A")
NAMES=("POS-01" "POS-02" "POS-03")
COUNT=100

PRODUCTS=(sugar flour rice milk bread eggs butter tomatoes onions potatoes bananas apples
  chicken beef pasta soap toothpaste detergent water softdrink coffee tea cornflakes
  salt pepper garlic ginger carrots cabbage peppers cucumber oranges grapes yogurt cheese
  biscuits chocolate chips juice beans ketchup tissue margarine honey jam)

GREETINGS=("good morning welcome to our store"
  "hello hi good afternoon how can i help"
  "good evening welcome please come in"
  "hi there welcome to quick mart"
  "morning sir what can i get for you"
  "afternoon madam please"
  "hello thanks for stopping by"
  "hi welcome how are you doing today")

ISSUES=("the price on the shelf was different from what you charged"
  "i bought this same item last week for less"
  "the expiry date on this bread is tomorrow can i get a fresh one"
  "you gave me the wrong change i gave you five thousand"
  "i asked for two of these not one"
  "the promotion says buy two get one free but its not reflecting"
  "the card reader declined my card but i have money"
  "can i return this i bought it yesterday and its defective")

CLOSINGS=("thank you very much have a nice day"
  "thanks for shopping with us please come again"
  "your receipt is here thank you madam"
  "bye bye see you next time"
  "thanks you have a blessed day"
  "thank you sir enjoy your evening"
  "please come back again we appreciate your business"
  "have a good one thank you for coming")

ARTIFACTS=("um" "uh" "ah" "so" "like" "you know" "i mean" "okay so" "let me see" "just a moment")
FILLERS=("[noise]" "[clears throat]" "[pause]" "[coins jingling]" "[beep]" "[receipt printing]")

MISPRON=( "cooking oil:cooking all" "cooking oil:cooking oel" "toothpaste:tooth paste"
  "tissue paper:issue paper" "chicken breast:chicken brest" "cornflakes:corn flakes"
  "bottled water:bottle water" "soft drink:sot drink" "groundnuts:ground nuts"
  "cabbage:cabbege" "cucumber:cucumba" "ketchup:catchup" "mayonnaise:mayonaise"
  "yogurt:yoghurt" "detergent:detergent" "margarine:margerine")

arr_contains() {
  local needle="$1" arr="$2"; [[ " ${arr} " == *" ${needle} "* ]]; return $?; }

rand_from() {
  local arr=("$@"); echo "${arr[RANDOM % ${#arr[@]}]}"; }

maybe_mispronounce() {
  local item="$1"
  for pair in "${MISPRON[@]}"; do
    local correct="${pair%%:*}" wrong="${pair##*:}"
    if [[ "$item" == "$correct" ]]; then
      (( RANDOM % 3 == 0 )) && echo "$wrong" && return
    fi
  done
  echo "$item"
}

gen_transcript() {
  local n=$(( RANDOM % 7 + 2 ))
  local used=()
  local text=""

  text+="$(rand_from "${GREETINGS[@]}")"
  (( RANDOM % 5 == 0 )) && text+=" $(rand_from "${FILLERS[@]}")"

  for (( i=0; i<n; i++ )); do
    while true; do
      local p="$(rand_from "${PRODUCTS[@]}")"
      if ! arr_contains "$p" "${used[*]}"; then used+=("$p"); break; fi
    done
    (( RANDOM % 4 == 0 )) && text+=" $(rand_from "${ARTIFACTS[@]}")"
    local spoken="$(maybe_mispronounce "$p")"
    local patterns=("i need ${spoken} please" "can i get one ${spoken}"
      "give me ${spoken}" "let me have two ${spoken}" "do you have ${spoken}"
      "i will take ${spoken} and" "add ${spoken} for me" "${spoken} how much is that"
      "one ${spoken} please" "i want to buy ${spoken}")
    text+=" $(rand_from "${patterns[@]}")"
  done

  (( RANDOM % 4 == 0 )) && text+=" $(rand_from "${ISSUES[@]}")"
  (( RANDOM % 5 == 0 )) && text+=" $(rand_from "${ARTIFACTS[@]}")"
  text+=" okay let me total that for you"

  local amt=$(( RANDOM % 24500 + 500 ))
  local totals=("that will be ${amt} shillings" "your total is ${amt} please"
    "that comes to ${amt} shillings sir" "the total is ${amt} madam")
  text+=" $(rand_from "${totals[@]}")"

  local payments=("here is my card" "i will pay with mobile money" "cash here you go"
    "let me use mpesa" "i have the exact amount" "card please")
  text+=" $(rand_from "${payments[@]}")"

  (( RANDOM % 5 == 0 )) && text+=" $(rand_from "${ARTIFACTS[@]}")"
  text+=" payment received thank you"
  text+=" $(rand_from "${CLOSINGS[@]}")"

  echo "$text"
}

OK=0; FAIL=0

for t in 0 1 2; do
  KEY="${KEYS[$t]}"
  NAME="${NAMES[$t]}"
  echo "--- $NAME ---"

  for i in $(seq 1 $COUNT); do
    local text="$(gen_transcript)"
    local words=$(echo "$text" | wc -w | tr -d ' ')
    local mins_ago=$(( RANDOM % 300 + 2 ))
    local dur=$(( RANDOM % 600 + 30 ))

    local started=$(date -u -d "${mins_ago} seconds ago" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -v-${mins_ago}S '+%Y-%m-%dT%H:%M:%SZ')
    local ended=$(date -u -d "${mins_ago} seconds ago + ${dur} seconds" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -v-${mins_ago}S -v+${dur}S '+%Y-%m-%dT%H:%M:%SZ')

    local json=$(printf '{"started_at":"%s","ended_at":"%s","raw_text":%s,"word_count":%d}' \
      "$started" "$ended" "$(echo "$text" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))')" "$words")

    local resp=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $KEY" \
      -d "$json")

    if [[ "$resp" == "200" || "$resp" == "201" ]]; then
      (( OK++ ))
    else
      (( FAIL++ ))
      echo "  #${i} ERR $resp"
    fi
  done
  echo "  $NAME done"
done

echo ""
echo "Results: $OK succeeded, $FAIL failed out of $(( COUNT * 3 ))"
