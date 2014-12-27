hivefs
======

##Requirements:
* Python 3.x

##Python modules:
* requests
* addict
* fusepy

(All are installable through pip)


##Functionality:
* Listing files and folders
* Reading files
* Renaming files and folders
* Setting folders to "Locked" or "Unlocked" (chmod 700 or 744)

Copying in or creating new files (uploading) is NOT working yet!
The upload process for the Hive.im API is a bit complicated and I haven't gotten it working yet.

If anyone out there knows how to do uploads via the Hive.im API using Python and the requests module (preferably), I'd be very interested to hear about it.

##Clarifications:
* Watching videos: Right now, when accessing a video file from the hivefs filesystem, it direct-downloads it as needed just like other files. This is not too good though if you're trying to watch a full HD video over a slow connection. Eventually, the encoded video stream (when available) will be used instead of downloading the file.

* More on file permissions: Hive.im only supports setting folders to "Locked" (private) or "Unlocked" (public), so the only supported permissions you can set from within this hivefs filesystem are 700 (Locked. Owner has full access, nobody else has any.) and 744 (Unlocked. Owner has full access, everyone else has read-only access).

##Usage:
    python3 hivefs.py /path/to/folder


##Contributing:
Right now, I will look at any "issues" that are submitted, but I will probably not be accepting pull requests for a while. The code is a real mess right now (but it works). Lots of uncommented stuff and some commented-out code that didn't work. I need to do some cleanup on it and make it readable before accepting pull requests.
