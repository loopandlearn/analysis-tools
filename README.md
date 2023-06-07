Nightscout CGM Uploader Script
This is a Bash script for uploading continuous glucose monitor (CGM) values to a Nightscout site.

Usage
The script expects five arguments:

INPUT_FILE: the path to the file containing the CGM values. Each value should be on a new line.
DELAY: the delay (in seconds) between each CGM value submission.
NIGHTSCOUT_ADDRESS: the URL of the Nightscout site.
API_KEY: the Nightscout API key.
You can call the script using the following format:

./cgm.sh <input file> <delay> <nightscout address> <api key> <nights>

For example:
./cgm.sh cgm_values.txt 30 https://my.url.com my-secret-api-key

If you do not provide all five arguments, the script will print a usage message and exit.

Description
The script starts by calculating the SHA1 hash of the API key. It then reads the CGM values from the input file line by line. For each value, it sends a HTTP POST request to the Nightscout API to upload the CGM value. It then waits for the specified delay before processing the next value. This continues until all values from the file have been uploaded.