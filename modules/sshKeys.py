from __future__ import print_function
from sys import version_info
import os, os.path, stat
import rh.common as common

_sshKeyTypes = [
    'ssh-rsa',
    'ssh-dss',
    'ssh-ed25519',
    'ecdsa-sha2-nistp256',
    'ecdsa-sha2-nistp384',
    'ecdsa-sha2-nistp521'
]

def _authorizedKeysCmd(config, args):
    args = args.split(' ')
    if args[0] == 'list':
        _listSshKeys(config, args[1:])
    elif args[0] == 'delete':
        _deleteSshKeys(config, args[1:])
    elif args[0] == 'add':
        _addSshKeys(config, args[1:])
    else:
        print("Usage: ssh-keys list|delete|add")

common.registerCmd('ssh-keys', _authorizedKeysCmd, "Manage authorized keys file")

# List SSH authorized keys
def _listSshKeys(config, args):
    full = False
    keysFile = os.path.expanduser("~/.ssh/authorized_keys")
    if len(args) > 0 and args[0] == 'full': full = True

    lines = []
    try:
        lines = _getAuthKeyFileLines()
    except IOError:
        print("No authorized keys file found")
        return

    # Print a pretty list
    print("\n#: Type - Key - Comment")
    print("-----------------------")
    for idx, line in enumerate(lines): _printKeyLine(idx+1, line, full)
    print()

# Delete an SSH authorized key
def _deleteSshKeys(config, args):
    keysFile = os.path.expanduser("~/.ssh/authorized_keys")
    if len(args) != 1: print("Usage: ssh-keys delete [key #]"); return
    # Get the key number to remove
    keyToDelete = args[0]
    if keyToDelete.isdigit(): keyToDelete = int(keyToDelete)

    lines = []
    try:
        lines = _getAuthKeyFileLines()
    except IOError:
        print("No authorized keys file found")
        return

    modified = False
    if keyToDelete > 0 and keyToDelete <= len(lines):
        del lines[keyToDelete-1]
        modified = True

    if modified:
        # Write new file
        with open(keysFile, 'w') as keyFile:
            keyFile.write('\n'.join(lines))
        print("Key removed")
    else:
        print("No key removed")

# Interactively add a new SSH authorized key
def _addSshKeys(config, args):
    lines = []
    try:
        lines = _getAuthKeyFileLines()
    except IOError:
        print("No authorized keys file found")
        return

    for i, ktype in enumerate(_sshKeyTypes): print("{}: {}".format(i+1, ktype))
    keyType = ''
    keyIndex = common.getInputNoHistory("Key type [1]: ")
    if not keyIndex.isdigit() or int(keyIndex) > len(_sshKeyTypes) or int(keyIndex) < 1:
        keyType = _sshKeyTypes[0]
    else:
        keyType = _sshKeyTypes[int(keyIndex)-1]

    keyHash = common.getInputNoHistory("Public key: ")
    if keyHash.find(' ') != -1: print("Bad public key"); return
    keyComment = common.getInputNoHistory("Key comment: ").strip().replace(' ', '_')

    print("\nKey type: {}".format(keyType))
    print("Key hash: {}".format(keyHash))
    print("Key comment: {}".format(keyComment))

    isOk = common.getInputNoHistory("Does this look correct? [Y/n]: ")
    if isOk.lower() == 'n':
        return

    print("Adding new key...")
    try:
        with open(keysFile, 'a') as keyFile:
            keyFile.write('\n' + ' '.join([keyType, keyHash, keyComment]))
    except IOError as e:
        print("Error adding new key")
        raise common.RhSilentException(str(e))
    print("New kew added")

# Gets the lines from an authorized_keys file and returns them as a list
# This function will create the .ssh directory and/or the authorized_keys file
# if they don't already exist and set the required Permissions.
def _getAuthKeyFileLines():
    sshDir = os.path.expanduser("~/.ssh")
    keysFile = os.path.join(sshDir, "authorized_keys")
    lines = []
    # Create file if doesn't exist
    if not os.path.isfile(keysFile):
        # Create directory if doesn't exist
        if not os.path.isdir(sshDir):
            os.mkdir(sshDir)
            os.chmod(sshDir, stat.S_IRWXU) # Permissions: 700
        open(keysFile, 'a').close() # Create and empty file
        os.chmod(keysFile, stat.S_IRUSR|stat.S_IWUSR) # Permissions: 600
        return []

    # If it does exist, read and return lines
    with open(keysFile, 'r') as keyFile:
        lines = _filterKeyFileLines(keyFile)
    return lines


# Filter authorized_keys lines by removing comments and empty lines
# Works on a file descriptor or list
def _filterKeyFileLines(lines):
    filteredList = []
    for line in lines:
        line = line.strip()
        if not line.startswith('#') and line != '':
            filteredList.append(line)
    return filteredList

def _printKeyLine(lineNum, line, full=False):
    line = line.split(' ')
    keyType = ''
    keyHash = ''
    keyComment = 'No comment'

    if len(line) == 4:
        keyType = line[1]
        keyHash = line[2]
        keyComment = line[3]
    elif len(line) == 3:
        keyType = line[0]
        keyHash = line[1]
        keyComment = line[2]
    elif len(line) == 2:
        keyType = line[0]
        keyHash = line[1]
    else:
        return

    if not full: keyHash = keyHash[-12:]
    print("{}: {} - {} - {}".format(lineNum, keyType, keyHash, keyComment))
