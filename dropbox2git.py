#!/usr/bin/env python3
import dropbox
import subprocess
import hashlib
import os

# No, I'm not leaking the token to you guys
TOKEN = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx"
FOLDER = "/e3_2016"


def getFolderContent(folderName):
    result = dbx.files_list_folder(folderName, recursive=True)
    content = []
    for entry in result.entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            content.append((entry.path_lower, "file"))
        elif isinstance(entry, dropbox.files.FolderMetadata):
            content.append((entry.path_lower, "folder"))
    return content


def getFileRevision(fileName):
    result = dbx.files_list_revisions(fileName, limit=100)
    revision = []
    for entry in result.entries:
        revision.append({"name": entry.name, "id": entry.rev, "date": entry.server_modified,
                         'client_date': entry.client_modified})
    return revision


def getFileHash(fileName):
    h = hashlib.md5()
    with open(fileName, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

dbx = dropbox.Dropbox(TOKEN)
fileHash = []
revisions = []
tmp = []

print("Getting content in folder %s" % (FOLDER))
folderContent = getFolderContent(FOLDER)
for f, x in folderContent:
    print("- [%s] %s" % (x, f))

for f, x in folderContent:
    f2 = f.replace("/e3_2016/", "")
    if x == "folder" and f2 != "" and f2 != "/e3_2016":
        print("Creating directory {}".format(f2))
        os.mkdir(f2)
    elif x == "file":
        print("Getting revisions for file {}".format(f))
        tmp = getFileRevision(f)
        print("Got {} revisions for file {}".format(len(tmp), f))
        for entry in tmp:
            entry['name'] = f
            entry['local_name'] = f2
        print(tmp)
        revisions.extend(tmp)

revisions.sort(key=lambda entry: entry["date"])

for entry in revisions:
    print("Downloaing file:%s rev:%s" % (entry['name'], entry['id']))
    dbx.files_download_to_file(entry['local_name'], "rev:%s" % (entry['id']))
    if not(getFileHash(entry['local_name']) in fileHash):
        subprocess.run(["git", "add", entry['local_name']])
        subprocess.run(["git", "commit", "-m", "Dropbox2Git: file: %s rev: %s client_modified: %s" % (entry['name'], entry['id'], entry['client_date'].isoformat()), "--date", entry['date'].isoformat()])
        fileHash.append(getFileHash(entry['local_name']))

# Push by yourself please, because I'm lazy
