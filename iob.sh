#!/bin/bash

# Check if correct number of arguments given
if [ "$#" -ne 3 ]; then
    echo "Nightscout IOB downloader"
    echo "Usage: $0 url start duration"
    echo "url is nightscout url i.e. https://my.nightscout.com"
    echo "start is date and time in utc format i.e. 2023-06-12T13:52:19Z"
    echo "duration is seconds from start, i.e. 3600 for an hour"
    echo "Pipe the result from the execution to a csv file in order to import to excel"
    exit 1
fi

# Parse arguments
url="$1"
start="$2"
duration="$3"

# Calculate end timestamp
end=$(date -u -v+${duration}S -j -f "%Y-%m-%dT%H:%M:%SZ" "${start}" "+%Y-%m-%dT%H:%M:%SZ")

# Make API request
response=$(curl -s "${url}/api/v1/devicestatus.json?find%5Bcreated_at%5D%5B%24gte%5D=${start}&find%5Bcreated_at%5D%5B%24lte%5D=${end}")

#echo "${url}/api/v1/devicestatus.json?find%5Bcreated_at%5D%5B%24gte%5D=${start}&find%5Bcreated_at%5D%5B%24lte%5D=${end}"
#echo $response

# Parse JSON and print results
echo $response | jq -r '.[] | "\(.created_at),\(.loop.iob.iob)"'

exit 0