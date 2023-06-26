# file_io.py
# this contains functions to read nightscout downloads from disk


def read_raw_nightscout(filename):
    noisy = 0
    if noisy:
        print("filename in read_json_file = ", filename)
    fp = open(filename, "r", encoding='UTF8')
    raw_content = fp.read()
    fp.close()
    # this next bit could be done with jq as part of the shell script
    # but is NOT done so now - change if decide to modify that
    # remove the beginning and ending []
    content = raw_content[1:-2]
    # break into separate json lines
    content = content.replace(',{"_id', '\n{"_id')
    return content
