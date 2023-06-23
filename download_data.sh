#!/bin/bash

# Check if correct number of arguments given
if [ "$#" -lt 3 ]; then
    echo "Nightscout IOB downloader"
    echo "Usage: $0 url start duration [api-key] [output-json-file]"
    echo "url is nightscout url i.e. https://my.nightscout.com"
    echo "start is date and time in utc format i.e. 2023-06-12T13:52:19Z"
    echo "duration is seconds from start, i.e. 3600 for an hour"
    echo "[api-key] is optional, use if the site requires it"
    echo "[query_name] is optional, if not provided, devicestatus is used"
    echo "[output_file] is optional, save the raw download (no jq parsing for iob) to file"
    echo "Pipe the result from the execution to a csv file in order to import to excel"
    exit 1
fi

# Parse arguments
url="$1"
start="$2"
duration="$3"
api_key="$4"
query_name="$5"
output_file="$6"

if [ -z "$query_name" ]; then
    query_name="devicestatus"
fi

# Calculate end timestamp
end=$(date -u -v+${duration}S -j -f "%Y-%m-%dT%H:%M:%SZ" "${start}" "+%Y-%m-%dT%H:%M:%SZ")

# Make API request
if [ -n "$api_key" ]; then
    API_SECRET=$(echo -n "$api_key" | shasum | awk '{print $1}')
    echo "${url}/api/v1/$query_name.json"
    response=$(curl -s -H "api-secret: ${API_SECRET}" "${url}/api/v1/$query_name.json?count=1000&find%5Bcreated_at%5D%5B%24gte%5D=${start}&find%5Bcreated_at%5D%5B%24lte%5D=${end}")
else
    response=$(curl -s "${url}/api/v1/$query_name.json?count=1000&find%5Bcreated_at%5D%5B%24gte%5D=${start}&find%5Bcreated_at%5D%5B%24lte%5D=${end}")
fi

# Output to file or Parse JSON and print results
if [ -n "$output_file" ]; then
    echo $response > $output_file
else
    echo $response | jq -r '.[] | "\(.created_at),\(.loop.iob.iob)"'
fi

exit 0