
import argparse
import sys
import numpy as np
class Node:
    '''
    Here is an arbitrary Node class that will form the basis of your decision
    tree. 
    Note:
        - the attributes provided are not exhaustive: you may add and remove
        attributes as needed, and you may allow the Node to take in initial
        arguments as well
        - you may add any methods to the Node class if desired 
    '''
    def __init__(self):
        self.left = None
        self.right = None
        self.attr = None
        self.vote = None
        self.n0 = 0
        self.n1 = 0   


def entropy_y(y):
    n = y.size
    if n == 0:
        return 0.0
    _, counts = np.unique(y, return_counts=True)
    p = counts / n
    return float(-np.sum(p * np.log2(p)))

def conditional(y, x):
    y = np.asarray(y)
    x = np.asarray(x)
    n = y.size
    if n == 0:
        return 0.0
    H = 0.0
    x_vals, x_counts = np.unique(x, return_counts=True)
    for i in range(len(x_vals)):
        xv = x_vals[i]
        cx = x_counts[i]
        mask = (x == xv)
        p_x = cx / n
        H += p_x * entropy_y(y[mask])
    return float(H)

def mutual_information(y, x):
    return float(entropy_y(y) - conditional(y, x))

def majority_vote(y) :
    n0 = int(np.sum(y == 0))
    n1 = int(np.sum(y == 1))
    return 1 if n1 >= n0 else 0

def error_rate(y_true, y_pred):
    if y_true.size == 0:
        return 0.0
    return float(np.mean(y_true != y_pred))

def build_tree(X, y, depth, max_depth, used_attrs):
    node = Node()
    node.n0 = int(np.sum(y == 0))
    node.n1 = int(np.sum(y == 1))
    if y.size == 0:
        node.vote = 1  
        return node
    if node.n0 == 0 or node.n1 == 0:
        node.vote = int(y[0])
        return node
    if depth >= max_depth:
        node.vote = majority_vote(y)
        return node
    d = X.shape[1]
    remaining = [j for j in range(d) if j not in used_attrs]
    if not remaining:
        node.vote = majority_vote(y)
        return node
    best_attr = None
    best_mi = -1
    for j in remaining:
        mi = mutual_information(y, X[:, j])
        if mi > best_mi + 1e-12 or (abs(mi - best_mi) <= 1e-12 and (best_attr is None or j < best_attr)):
            best_mi = mi
            best_attr = j
    if best_attr is None or best_mi <= 1e-12:
        node.vote = majority_vote(y)
        return node
    
    node.attr = best_attr
    left_mask = (X[:, best_attr] == 0)
    right_mask = (X[:, best_attr] == 1)

    if not np.any(left_mask) or not np.any(right_mask):
        node.attr = None
        node.vote = majority_vote(y)
        return node

    new_used = set(used_attrs)
    new_used.add(best_attr)
    node.left = build_tree(X[left_mask], y[left_mask], depth + 1, max_depth, new_used)
    node.right = build_tree(X[right_mask], y[right_mask], depth + 1, max_depth, new_used)
    return node

def predict_one(node, x_row):
    cur = node
    while cur.attr is not None:
        if int(x_row[cur.attr]) == 0:
            cur = cur.left
        else:
            cur = cur.right
        if cur is None:
            return 1
    return int(cur.vote)

def predict_all(node, X):
    return np.array([predict_one(node, X[i]) for i in range(X.shape[0])], dtype=int)


def print_tree(node, file, feature_names, depth=0):
    if depth == 0:
        file.write("[" + str(node.n0) + " 0/" + str(node.n1) + " 1]\n")
    if node.attr is None:
        return

    attr_name = feature_names[node.attr]
    indent = "| " * (depth + 1)
    file.write(indent + attr_name + " = 0: [" +
               str(node.left.n0) + " 0/" +
               str(node.left.n1) + " 1]\n")
    if node.left.attr is not None:
        print_tree(node.left, file, feature_names, depth + 1)

    file.write(indent + attr_name + " = 1: [" +
               str(node.right.n0) + " 0/" +
               str(node.right.n1) + " 1]\n")
    if node.right.attr is not None:
        print_tree(node.right, file, feature_names, depth + 1)

def load_tsv(path):
    with open(path, "r", encoding="utf-8") as f:
        header = f.readline().strip()
    cols = header.split("\t")
    data = np.loadtxt(path, delimiter="\t", skiprows=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    X = data[:, :-1].astype(int)
    y = data[:, -1].astype(int)
    feature_names = cols[:-1]
    return feature_names, X, y

def write_predictions(path, y_pred):
    with open(path, "w", encoding="utf-8") as f:
        for v in y_pred:
            f.write(f"{int(v)}\n")

def write_metrics(path, train_err, test_err):
    with open(path, "w", encoding="utf-8") as f:
        f.write("error(train): " + format(train_err, ".6f") + "\n")
        f.write("error(test): " + format(test_err, ".6f") + "\n")



if __name__ == '__main__':
    # This takes care of command line argument parsing for you!
    # To access a specific argument, simply access args.<argument name>.
    # For example, to get the train_input path, you can use `args.train_input`.
    parser = argparse.ArgumentParser()
    parser.add_argument("train_input", type=str, help='path to training input .tsv file')
    parser.add_argument("test_input", type=str, help='path to the test input .tsv file')
    parser.add_argument("max_depth", type=int, 
                        help='maximum depth to which the tree should be built')
    parser.add_argument("train_out", type=str, 
                        help='path to output .txt file to which the feature extractions on the training data should be written')
    parser.add_argument("test_out", type=str, 
                        help='path to output .txt file to which the feature extractions on the test data should be written')
    parser.add_argument("metrics_out", type=str, 
                        help='path of the output .txt file to which metrics such as train and test error should be written')
    parser.add_argument("print_out", type=str,
                        help='path of the output .txt file to which the printed tree should be written')
    args = parser.parse_args()
    feature_names, X_train, y_train = load_tsv(args.train_input)
    _, X_test, y_test = load_tsv(args.test_input)   
    #Here's an example of how to use argparse
    print_out = args.print_out
    dTree = build_tree(X_train, y_train, depth=0, max_depth=args.max_depth, used_attrs=set())
    yhat_train = predict_all(dTree, X_train)
    yhat_test = predict_all(dTree, X_test)

    write_predictions(args.train_out, yhat_train)
    write_predictions(args.test_out, yhat_test)
    train_err = error_rate(y_train, yhat_train)
    test_err = error_rate(y_test, yhat_test)
    write_metrics(args.metrics_out, train_err, test_err)
    with open(args.print_out, "w", encoding="utf-8") as f:
        print_tree(dTree, f, feature_names)
    #Here is a recommended way to print the tree to a file
    # with open(print_out, "w") as file:
    #     print_tree(dTree, file)