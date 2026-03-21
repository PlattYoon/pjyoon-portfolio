import numpy as np
import argparse


def sigmoid(x : np.ndarray):
    """
    Implementation of the sigmoid function.

    Parameters:
        x (np.ndarray): Input np.ndarray.

    Returns:
        An np.ndarray after applying the sigmoid function element-wise to the
        input.
    """
    out = np.empty_like(x, dtype=float)
    pos = (x >= 0)
    neg = ~pos
    out[pos] = 1.0 / (1.0 + np.exp(-x[pos]))
    ex = np.exp(x[neg])
    out[neg] = ex / (1.0 + ex)
    return out


def train(
    theta : np.ndarray, # shape (?,)
    X : np.ndarray,     # shape (?, ?)
    y : np.ndarray,     # shape (?,)
    num_epoch : int, 
    learning_rate : float
) -> None:
    N = X.shape[0]
    for _ in range(num_epoch):
        for i in range(N):
            xi = X[i]               
            yi = y[i]               
            pi = sigmoid(np.array([xi @ theta]))[0]  
            grad = (pi - yi) * xi
            theta -= learning_rate * grad



def predict(
    theta : np.ndarray, # shape (?,)
    X : np.ndarray      # shape (?, ?)
) -> np.ndarray:
    probs = sigmoid(X @ theta)
    return (probs >= 0.5).astype(int)


def compute_error(
    y_pred : np.ndarray, 
    y : np.ndarray
) -> float:
    return float(np.mean(y_pred != y))

def load_formatted_tsv(path: str):
    data = np.loadtxt(path, delimiter="\t", dtype=float)
    y = data[:, 0].astype(int)
    X = data[:, 1:]
    return y, X

def add_intercept(X: np.ndarray):
    N = X.shape[0]
    return np.hstack([np.ones((N, 1)), X])


def write_labels(path: str, y_pred: np.ndarray):
    with open(path, "w", encoding="utf-8") as f:
        for v in y_pred:
            f.write(f"{int(v)}\n")


def write_metrics(path: str, train_err: float, test_err: float):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"error(train): {train_err:.6f}\n")
        f.write(f"error(test): {test_err:.6f}\n")


def compute_nll(
    theta: np.ndarray,
    X: np.ndarray,
    y: np.ndarray
) -> float:
    probs = sigmoid(X @ theta)
    probs = np.clip(probs, 1e-15, 1 - 1e-15)
    return float(-np.mean(y * np.log(probs) + (1 - y) * np.log(1 - probs)))


def train_and_record(
    theta: np.ndarray,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    num_epoch: int,
    learning_rate: float
):
    N = X_train.shape[0]
    train_nll_history = []
    val_nll_history = []

    for _ in range(num_epoch):
        for i in range(N):
            xi = X_train[i]
            yi = y_train[i]
            pi = sigmoid(np.array([xi @ theta]))[0]
            grad = (pi - yi) * xi
            theta -= learning_rate * grad

        train_nll_history.append(compute_nll(theta, X_train, y_train))
        val_nll_history.append(compute_nll(theta, X_val, y_val))

    return train_nll_history, val_nll_history

if __name__ == '__main__':
    # This takes care of command line argument parsing for you!
    # To access a specific argument, simply access args.<argument name>.
    # For example, to get the learning rate, you can use `args.learning_rate`.
    parser = argparse.ArgumentParser()
    parser.add_argument("train_input", type=str, help='path to formatted training data')
    parser.add_argument("validation_input", type=str, help='path to formatted validation data')
    parser.add_argument("test_input", type=str, help='path to formatted test data')
    parser.add_argument("train_out", type=str, help='file to write train predictions to')
    parser.add_argument("test_out", type=str, help='file to write test predictions to')
    parser.add_argument("metrics_out", type=str, help='file to write metrics to')
    parser.add_argument("num_epoch", type=int,
                        help='number of epochs of stochastic gradient descent to run')
    parser.add_argument("learning_rate", type=float,
                        help='learning rate for stochastic gradient descent')
    args = parser.parse_args()

    # Load
    y_train, X_train = load_formatted_tsv(args.train_input)
    y_test, X_test = load_formatted_tsv(args.test_input)

    # Add intercept
    X_train_i = add_intercept(X_train)
    X_test_i = add_intercept(X_test)

    # Init theta to zeros
    D_plus_1 = X_train_i.shape[1]
    theta = np.zeros(D_plus_1, dtype=float)

    # Train
    train(theta, X_train_i, y_train, args.num_epoch, args.learning_rate)

    # Predict
    yhat_train = predict(theta, X_train_i)
    yhat_test = predict(theta, X_test_i)

    # Error
    train_err = compute_error(yhat_train, y_train)
    test_err = compute_error(yhat_test, y_test)

    # Write outputs
    write_labels(args.train_out, yhat_train)
    write_labels(args.test_out, yhat_test)
    write_metrics(args.metrics_out, train_err, test_err)