import sys
import numpy as np

def read_labels(path):
    data = np.genfromtxt(path, delimiter="\t", dtype=str, skip_header=1)
    return data[:, -1].astype(int)

def majority_vote(y_train):
    vals, counts = np.unique(y_train, return_counts=True)
    max_count = counts.max()
    tied = vals[counts == max_count]
    return int(tied.max())

def write_predict(prediction, filename, length):
    with open(filename, "w") as file:
        for _ in range(length):
            file.write(str(prediction) + "\n")

def error_rate(y_true, prediction):
    return float(np.mean(y_true != prediction))

def main():
    train_in, test_in, train_out, test_out, metrics_out = sys.argv[1:6]
    y_train = read_labels(train_in)
    y_test = read_labels(test_in)
    pred = majority_vote(y_train)
    write_predict(pred, train_out, len(y_train))
    write_predict(pred, test_out, len(y_test))
    err_train = error_rate(y_train, pred)
    err_test = error_rate(y_test, pred)
    with open(metrics_out, "w", encoding="utf-8") as f:
        f.write(f"error(train): {err_train:.6f}\n")
        f.write(f"error(test): {err_test:.6f}\n")

if __name__ == "__main__":
    main()