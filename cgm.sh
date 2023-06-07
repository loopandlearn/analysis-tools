#!/bin/bash

if [ "$#" -ne 5 ]; then
    echo "Usage: ./cgm.sh <input file> <delay> <nightscout address> <api key>"
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
  echo "CGM Value: $line"
  
  CURRENT_TIME=$(date +%s)000

  curl -X POST -H "api-secret: $API_SECRET" -H "Content-Type: application/json" -d "{\"type\":\"sgv\",\"sgv\":$line,\"date\":$CURRENT_TIME,\"dateString\":\"$(date -u -Iseconds)\",\"direction\":\"Flat\",\"device\":\"dexcom\",\"filtered\":$line,\"unfiltered\":$line,\"rssi\":100,\"noise\":1,\"sysTime\":\"$(date -u -Iseconds)\"}" $NIGHTSCOUT_ADDRESS/api/v1/entries
  sleep $DELAY
done < "$INPUT_FILE"