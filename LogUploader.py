#!/usr/local/bin/managed_python3
import json
import os
import plistlib
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED

import objc
import requests
from Foundation import NSBundle, NSString
from SystemConfiguration import SCDynamicStoreCopyConsoleUser

IOKit_bundle = NSBundle.bundleWithIdentifier_('com.apple.framework.IOKit')

functions = [("IOServiceGetMatchingService", b"II@"),
             ("IOServiceMatching", b"@*"),
             ("IORegistryEntryCreateCFProperty", b"@I@@I"),
            ]

objc.loadBundleFunctions(IOKit_bundle, globals(), functions)

# Set Variables
JamfPrefs = "/Library/Preferences/com.jamfsoftware.jamf.plist"
encodedAuth = sys.argv[4]


# User Variables
wantedLogs = sys.argv[5]

# Intentionally Blank Variables
LoggedInUser = ""
computerUDID = ""
serialNumber = ""
jssURL = ""
authToken = ""
compID = ""


# Date & Time
now = datetime.now()
timeStamp = now.strftime("%Y-%m-%d-%H-%M-%S")


# Get Logged in User
def getLoggedInUser():
    global LoggedInUser
    LoggedInUser = SCDynamicStoreCopyConsoleUser(None, None, None)[0]
    return LoggedInUser


# Required for UUID & Serial Number
def io_key(keyname):
    return IORegistryEntryCreateCFProperty(IOServiceGetMatchingService(0, IOServiceMatching("IOPlatformExpertDevice".encode("utf-8"))), NSString.stringWithString_(keyname), None, 0)


# Get UUID
def get_hardware_uuid():
    global computerUDID
    computerUDID = io_key("IOPlatformUUID")
    return computerUDID


# Get Serial Number
def get_hardware_serial():
    global serialNumber
    serialNumber = io_key("IOPlatformSerialNumber")
    return serialNumber


# Get Shutdown Codes
def get_ShutdownCodes():
    global wantedLogs
    global shutdownLog
    shutdownLog = "/tmp/shutdown_cause-" + timeStamp + ".txt"
    shutdownCode = "log show --predicate 'eventMessage contains \"Previous shutdown cause\"' --last 72h >> " + shutdownLog
    os.system(shutdownCode)
    wantedLogs = wantedLogs + ", " + shutdownLog  # type: ignore
    return shutdownLog


# Zip required Log files
def zip_log_files():
    global zippedFile
    logFiles = wantedLogs.split(', ')
    zippedFile = timeStamp + "_" + LoggedInUser + "_" + serialNumber + ".zip"
    with zipfile.ZipFile("/tmp/" + zippedFile, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for logFile in logFiles:
            if Path(logFile).is_file():
                archive.write(logFile)
            else:
                print(logFile + " not found")


# Get JSS Url and remove / from end if there
def GetjssURL():
    global jssURL
    if os.path.exists(JamfPrefs):
        with open(JamfPrefs, "rb") as f:
            pl = plistlib.load(f)
            OrgjssURL = (pl.get("jss_url"))
            if OrgjssURL[-1] == "/":
                jssURL = OrgjssURL[:-1]
            else:
                jssURL = OrgjssURL
            return jssURL


# Create Bearer Token
def CreateBearerToken():
    global authToken
    url = jssURL + "/api/v1/auth/token"

    payload = {}
    headers = {
        'Authorization': 'Basic ' + encodedAuth
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    data = json.loads(response.text)
    # return data['token']
    authToken = data["token"]
    return authToken


# Refresh Bearer Token
def RefreshBearerToken():
    url = jssURL + "/api/v1/auth/keep-alive"

    payload = {}
    headers = {
        'Authorization': 'Bearer ' + authToken
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


# Invalidate Token
def InvalidateBearerToken():
    url = jssURL + "/api/v1/auth/invalidate-token"

    payload = {}
    headers = {
        'Authorization': 'Bearer ' + authToken
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


# Check UUID in Jamf
def checkComputerUUID():
    global compID
    url = jssURL + '/JSSResource/computers/udid/' + computerUDID
    payload = {}
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/xml',
        'Authorization': 'Bearer ' + authToken
    }

    response = requests.request("GET", url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        compID = data['computer']['general']['id']
        print("Computer is in Jamf")
        return (compID)
    else:
        print("Computer not found: Status code:", response.status_code)
        exit()


# Upload Files to JSS
def fileUpload():

    url = jssURL + "/JSSResource/fileuploads/computers/id/" + str(compID)

    upLoadFile = "/tmp/" + zippedFile

    CurlURL = "/usr/bin/curl --request POST " + url + " --header 'Authorization: Bearer '" + authToken + " --form name=@" + upLoadFile + ""
    os.system(CurlURL)


# Cleanup
def cleanUp():
    zippedList = ["/tmp/" + zippedFile]
    for zipFile in zippedList:
        if Path(zipFile).is_file():
            file_path = Path(zipFile)
            file_path.unlink()
        else:
            print(zipFile + " not found")


# Main Bits
def main():
    getLoggedInUser()
    get_hardware_uuid()
    get_hardware_serial()
    get_ShutdownCodes()
    zip_log_files()
    GetjssURL() # Disable for Testing
    CreateBearerToken()
    checkComputerUUID() # Disable for Testing
    fileUpload()
    cleanUp()
    InvalidateBearerToken()


if __name__ == "__main__":
    main()
