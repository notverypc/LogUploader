LogUploader uploads required logs to JamfPro.

Inspired greatly by this https://github.com/kc9wwh/logCollection 
Serial Number and UUID thanks to https://gist.github.com/erikng/46646ff81e55b42e5cfc 

I wanted to try and build this in python.

Requiredments:

MacAdmins Python https://github.com/macadmins/python

## What does it do:
As well as finding the required log files, it will also collect the shutdown codes for the last 72hrs.
These are then zipped and uploaded to JamfPro as an attachment to the device record.

## How to Use:
1. Upload the LogUploader.py script to your JamfPro.
2. Create a policy to run the script and include the following information:
   - Parameter 4 - encoded Authentication for JamfPro.
   - Parameter 5 - Log locations separated by a comma (/private/var/log/install.log, /private/var/log/jamf.log)

We have the policy run via Self-Service.

To notify us when someone has run the LogUploader the policy has an additional script that sends us a slack notification.

![Slack_Not](https://user-images.githubusercontent.com/585423/205630526-f1b9cd26-49f5-4d2b-a516-99d51c076ae2.png)

## Nice to dos.. 
- Make the shutdown codes "optional".
- Add device url to slack notification.
