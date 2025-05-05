def GetRefAndKey(linkString):
    if linkString.startswith(("*.", "!.")):
        linkString = linkString[2:]

    key = None
    s = linkString.split('#')
    ref = s[0]
    if len(s) == 2:
        key = s[1]

    return (ref, key)

