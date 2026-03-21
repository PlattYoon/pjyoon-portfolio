# primer length
def primerLength(seq):
    return len(seq)

# GC content (percentage)
def primerGC(seq):
    length = len(seq)
    gcCount = 0
    for i in range(length):
        if seq[i] == 'C' or seq[i] == 'G':
            gcCount += 1
    return (gcCount/length) * 100

# longest repeat
def longestRepeat(seq):
    maxRepeat = 0
    length = len(seq)
    if length >= 2:
        for i in range(length - 1):
            currPair = seq[i:i+1]
            currRepeat = 1
            next = i + 2
            while next < length - 1 and seq[next:next + 1] == currPair:
                currRepeat += 1
                next = next + 2
            maxRepeat = max(currRepeat, maxRepeat)
    return maxRepeat

# longest run
def longestRun(seq):
    maxRun = 1
    currRun = 1
    for  i in range(len(seq) - 1):
        if seq[i] == seq[i + 1]:
            currRun += 1
        else:
            currRun = 1
        if currRun >= maxRun:
                maxRun = currRun
    return maxRun