***Nightscout CGM Uploader Script***

This is a Bash script for uploading continuous glucose monitor (CGM) values to a Nightscout site.

Usage
The script expects four arguments:

__INPUT_FILE__: the path to the file containing the CGM values. Each value should be on a new line.  
__DELAY__: The delay (in seconds) between each CGM value submission. For example, use 300 for a 5-minute interval.  
__NIGHTSCOUT_ADDRESS__: the URL of the Nightscout site.  
__API_KEY__: the Nightscout API key.  


You can call the script using the following format:
```bash
./cgm.sh <input file> <delay> <nightscout address> <api key>
```
For example:
```bash
./cgm.sh cgm_values.txt 300 https://my.url.com my-secret-api-key
```

If you do not provide all five arguments, the script will print a usage message and exit.

**Description**  
The script starts by calculating the SHA1 hash of the API key. It then reads the CGM values from the input file line by line. For each value, it sends a HTTP POST request to the Nightscout API to upload the CGM value. It then waits for the specified delay before processing the next value. This continues until all values from the file have been uploaded.