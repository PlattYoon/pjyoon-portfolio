import csv
import numpy as np
import argparse

VECTOR_LEN = 300   # Length of glove vector
MAX_WORD_LEN = 64  # Max word length in dict.txt and glove_embeddings.txt

################################################################################
# We have provided you the functions for loading the tsv and txt files. Feel   #
# free to use them! No need to change them at all.                             #
################################################################################


def load_tsv_dataset(file):
    """
    Loads raw data and returns a tuple containing the reviews and their ratings.

    Parameters:
        file (str): File path to the dataset tsv file.

    Returns:
        An np.ndarray of shape N. N is the number of data points in the tsv file.
        Each element dataset[i] is a tuple (label, review), where the label is
        an integer (0 or 1) and the review is a string.
    """
    dataset = np.loadtxt(file, delimiter='\t', comments=None, encoding='utf-8',
                         dtype='l,O')
    return dataset


def load_feature_dictionary(file):
    """
    Creates a map of words to vectors using the file that has the glove
    embeddings.

    Parameters:
        file (str): File path to the glove embedding file.

    Returns:
        A dictionary indexed by words, returning the corresponding glove
        embedding np.ndarray.
    """
    glove_map = dict()
    with open(file, encoding='utf-8') as f:
        read_file = csv.reader(f, delimiter='\t')
        for row in read_file:
            word, embedding = row[0], row[1:]
            glove_map[word] = np.array(embedding, dtype=float)
    return glove_map

_PUNCT = ".,!?;:\"'()[]{}<>/\\|@#$%^&*_+=~`"

def reviews(review: str, glove_map: dict):
    words = review.strip().split()
    vecs = []
    for w in words:
        w = w.strip(_PUNCT)
        if not w:
            continue
        if len(w) > MAX_WORD_LEN:
            w = w[:MAX_WORD_LEN]
        if w in glove_map:
            vecs.append(glove_map[w])
    if len(vecs) == 0:
        return np.zeros(VECTOR_LEN, dtype=float)
    return np.mean(np.vstack(vecs), axis=0)


def write_dataset(dataset, glove_map, out_path: str):
    with open(out_path, "w", encoding="utf-8") as f:
        for (label, review) in dataset:
            feat = reviews(str(review), glove_map)
            parts = [f"{float(label):.6f}"] + [f"{v:.6f}" for v in feat.tolist()]
            f.write("\t".join(parts) + "\n")


if __name__ == '__main__':
    # This takes care of command line argument parsing for you!
    # To access a specific argument, simply access args.<argument name>.
    # For example, to get the train_input path, you can use `args.train_input`.
    parser = argparse.ArgumentParser()
    parser.add_argument("train_input", type=str, help='path to training input .tsv file')
    parser.add_argument("validation_input", type=str, help='path to validation input .tsv file')
    parser.add_argument("test_input", type=str, help='path to the input .tsv file')
    parser.add_argument("feature_dictionary_in", type=str, 
                        help='path to the GloVe feature dictionary .txt file')
    parser.add_argument("train_out", type=str, 
                        help='path to output .tsv file to which the feature extractions on the training data should be written')
    parser.add_argument("validation_out", type=str, 
                        help='path to output .tsv file to which the feature extractions on the validation data should be written')
    parser.add_argument("test_out", type=str, 
                        help='path to output .tsv file to which the feature extractions on the test data should be written')
    args = parser.parse_args()
    glove_map = load_feature_dictionary(args.feature_dictionary_in)

    train_data = load_tsv_dataset(args.train_input)
    val_data = load_tsv_dataset(args.validation_input)
    test_data = load_tsv_dataset(args.test_input)

    write_dataset(train_data, glove_map, args.train_out)
    write_dataset(val_data, glove_map, args.validation_out)
    write_dataset(test_data, glove_map, args.test_out)