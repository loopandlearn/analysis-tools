#!/bin/bash

set -u

# 1. Update token
#To get token:
# Mongo DB -> profile -> loopSettings -> deviceToken
# Sort with { startDate: -1 }
DEVICE_TOKEN=""

# 2. Update Team ID
TEAM_ID=""

# 3. Update Auth Key ID
AUTH_KEY_ID=""

# 4. Uncomment one of these
APNS_HOST_NAME=api.sandbox.push.apple.com #Use for Xcode debug builds
#APNS_HOST_NAME=api.push.apple.com #Use for AppCenter builds

# 5. Add the auth key in file to the same directory
TOKEN_KEY_FILE_NAME=./AuthKey_${AUTH_KEY_ID}.p8
TOPIC=com.${TEAM_ID}.loopkit.Loop

function authenticationToken() {
  # confirm handshake
  $(echo -n | openssl s_client -connect "${APNS_HOST_NAME}":443 >/dev/null 2>&1)

  # confirm comm with real data (FIXME, add some real samples for Nightscout data here)
  JWT_ISSUE_TIME=$(date +%s)
  JWT_HEADER=$(printf '{ "alg": "ES256", "kid": "%s" }' "${AUTH_KEY_ID}" | openssl base64 -e -A | tr -- '+/' '-_' | tr -d =)
  JWT_CLAIMS=$(printf '{ "iss": "%s", "iat": %d }' "${TEAM_ID}" "${JWT_ISSUE_TIME}" | openssl base64 -e -A | tr -- '+/' '-_' | tr -d =)
  JWT_HEADER_CLAIMS="${JWT_HEADER}.${JWT_CLAIMS}"
  JWT_SIGNED_HEADER_CLAIMS=$(printf "${JWT_HEADER_CLAIMS}" | openssl dgst -binary -sha256 -sign "${TOKEN_KEY_FILE_NAME}" | openssl base64 -e -A | tr -- '+/' '-_' | tr -d =)
  AUTHENTICATION_TOKEN="${JWT_HEADER}.${JWT_CLAIMS}.${JWT_SIGNED_HEADER_CLAIMS}"

  echo "$AUTHENTICATION_TOKEN"
}

# This will show a push notification in Loop. Note you may need to swipe down to see it if Loop was open while received.
function sayHello() {
  
  AUTHENTICATION_TOKEN="$(authenticationToken)"
  if [ -z "$AUTHENTICATION_TOKEN" ]; then
    echo "Error: Authentication token is empty!"
    return 1
  fi

  FAKE_DATA='{"aps":{"alert":"Sugar85","content-available":1,"interruption-level":"time-sensitive"}}'

  echo "Topic: $TOPIC"
  echo "Auth Token: $AUTHENTICATION_TOKEN"
  echo "Payload: $FAKE_DATA"
  echo "APNS Host: $APNS_HOST_NAME"
  echo "Device Token: $DEVICE_TOKEN"

  # Ensure all variables are defined
  if [ -z "$TOPIC" ] || [ -z "$APNS_HOST_NAME" ] || [ -z "$DEVICE_TOKEN" ]; then
    echo "Error: Required variables are missing!"
    return 1
  fi
  # Use properly quoted variables in curl command
  curl -v \
    --header "apns-topic: $TOPIC" \
    --header "apns-push-type: alert" \
    --header "authorization: bearer $AUTHENTICATION_TOKEN" \
    --header "Content-Type: application/json" \
    --data "$FAKE_DATA" \
    --http2 \
    "https://${APNS_HOST_NAME}/3/device/${DEVICE_TOKEN}"
}

function backgroundPush(){
  AUTHENTICATION_TOKEN="$(authenticationToken)"
  FAKE_DATA='{"aps":{"alert":"test","content-available":1},"interruption-level":"time-sensitive"}'
  curl -v \
    --header "apns-topic: $TOPIC" \
    --header "apns-push-type: background" \
    --header "apns-priority: 5" \
    --header "authorization: bearer $AUTHENTICATION_TOKEN" \
    --data-raw ${FAKE_DATA} \
    --http2 \
    https://${APNS_HOST_NAME}/3/device/${DEVICE_TOKEN}
}

# Check if the function exists
  if [ $# -gt 0 ]; then
#if declare -f "$1" > /dev/null
  # call arguments verbatim
  "$@"
else
  # Show a helpful error
  echo "Functions Available:"
  typeset -f | awk '!/^main[ (]/ && /^[^ {}]+ *\(\)/ { gsub(/[()]/, "", $1); print $1}'
  exit 1
fi


