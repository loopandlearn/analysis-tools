#!/bin/bash

if ! command -v shasum &> /dev/null
then
    echo "shasum could not be found, please install it first"
    exit
fi

if [ "$#" -eq 5 ]; then
    NOISE_PERCENT="$5"
    echo "NOISE_PERCENT = $NOISE_PERCENT"
    ADD_NOISE="1"
else
    NOISE_PERCENT=0
    ADD_NOISE="0"
fi

if [ "$#" -lt 4 ]; then
    echo "Usage: ./cgm.sh <input file> <delay> <nightscout address> <api key> [noise-percent]"
    echo "   Note noise-percent is optional, must be an integer and is applied using a random number in the script"
    exit 1
fi

INPUT_FILE=$1
DELAY=$2
NIGHTSCOUT_ADDRESS=$3
API_KEY=$4

API_SECRET=$(echo -n "$API_KEY" | shasum | awk '{print $1}')
echo "API Secret: $API_SECRET"

while IFS= read -r line
do
  if [ ${NOISE_PERCENT} -ne "0" ]; then
    random_number=$RANDOM
    random_noise=$(($random_number - 16535))
    noise_to_add=$((($line * $NOISE_PERCENT * $random_noise)/1653500))
    cgm_value=$(($line + $noise_to_add))
    # echo "Next CGM Value, cgm_with_noise (random_number, noise) = $line, ${cgm_value} (${random_number}, ${noise_to_add})"
    echo "Next CGM Value, cgm_with_noise = $line, ${cgm_value}"
  else
    cgm_value=$line
    echo "Next CGM Value = $cgm_value"
  fi
  
  CURRENT_TIME=$(date +%s)000

  curl -X POST -H "api-secret: $API_SECRET" -H "Content-Type: application/json" -d "{\"type\":\"sgv\",\"sgv\":$cgm_value,\"date\":$CURRENT_TIME,\"dateString\":\"$(date -u -Iseconds)\",\"direction\":\"Flat\",\"device\":\"dexcom\",\"filtered\":$cgm_value,\"unfiltered\":$cgm_value,\"rssi\":100,\"noise\":1,\"sysTime\":\"$(date -u -Iseconds)\"}" $NIGHTSCOUT_ADDRESS/api/v1/entries
  sleep $DELAY
  echo ""
done < "$INPUT_FILE"
