import skimage as ski
import matplotlib.pyplot as plt
from skimage.color import rgb2gray
from skimage import color, feature, io, measure
import os
from scipy import ndimage as ndi
import re


def get_images(image_dir=None, with_labels=False):
    if image_dir is None:
        image_dir = input("Input path to images folder: ")

    suffixes = (".jpg", ".png")
    for f in os.listdir(image_dir):
        if f.lower().endswith(suffixes):
            image_path = os.path.join(image_dir, f)
            image = io.imread(image_path)

            if with_labels:
                # Extract group and treatment numbers
                match = re.search(r'G(\d+)_.*?T([0-9]+(?:\.[0-9]+)?)_', f)
                if match:
                    group_num = int(match.group(1))
                    treatment_num = float(match.group(2))
                else:
                    group_num = None
                    treatment_num = None

                if group_num <= 6:
                    day = 1
                else:
                    day = 2
                print("Loaded Image")
                yield (image, group_num, treatment_num, day, f)
            else:
                yield image

    """
    if image_dir is None:
        image_dir = input("Input path to images folder: ")

    suffixes =(".jpg", ".png")
    for f in os.listdir(image_dir):

        if f.lower().endswith(suffixes):
            yield io.imread(os.path.join(image_dir, f))
    """


if __name__ == "__main__":
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.imshow(next(get_images()))
    ax.set_axis_off()
    plt.show()
