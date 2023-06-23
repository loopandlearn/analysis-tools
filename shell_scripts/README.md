# Collection of Nightscout Scripts

1. [Nightscout CGM Uploader Script](#nightscout-cgm-uploader-script)
1. [Nightscout IOB Downloader Script](#nightscout-iob-downloader-script)
1. [Nightscout Data Downloader Script](#nightscout-data-downloader-script)

## Nightscout CGM Uploader Script

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

## Nightscout IOB Downloader Script

This script downloads devicedata from Nightscout and parses it to report time and IOB.

The command line arguments are:

* URL
* start_date (UTC: example 2023-06-19T23:19:00Z)
* duration (time in seconds to include after start_date)
* api_secret (if required)

If saving to a file is desired, simply pipe it to the filename you choose.

## Nightscout Data Downloader Script

This scrip is more generic - it accepts the query name for download and writes to a file for later python processing.

Script name: download_data.sh

The command line arguments are:

* URL
* start_date (UTC: example 2023-06-19T23:19:00Z)
* duration (time in seconds to include after start_date)
* api_secret (if required, if not, enter -)
* query_name (optional, default is devicestatus)
* output_file (optional, without it results go to stdout)