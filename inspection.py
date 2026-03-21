#!/usr/bin/env python3
import sys
import numpy as np

def entropy_from_labels(y):
    y = np.asarray(y)
    n = y.size
    if n == 0:
        return 0.0
    _, counts = np.unique(y, return_counts=True)
    p = counts / n
    return float(-np.sum(p * np.log2(p)))

def majority_vote_error(y):
    y = np.asarray(y)
    n = y.size
    if n == 0:
        return 0.0
    count0 = np.sum(y == 0)
    count1 = np.sum(y == 1)
    pred = 1 if count1 >= count0 else 0
    return float(np.mean(y != pred))

def main():
    if len(sys.argv) != 3:
        print("Error Risen")
        sys.exit(1)
    in_path = sys.argv[1]
    out_path = sys.argv[2]
    data = np.loadtxt(in_path, delimiter="\t", dtype = int, skiprows=1)
    y = data[:, -1].astype(int)
    ent = entropy_from_labels(y)
    err = majority_vote_error(y)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"entropy: {ent:.6f}\n")
        f.write(f"error: {err:.6f}\n")

if __name__ == "__main__":
    main()
