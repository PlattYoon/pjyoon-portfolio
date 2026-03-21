import skimage as ski
import matplotlib.pyplot as plt
from skimage.color import rgb2gray
from skimage import color, feature, io, measure
import os
from scipy import ndimage as ndi


def get_images(image_dir=None):
    if image_dir is None:
        image_dir = input("Input path to images folder: ")

    suffixes =(".jpg", ".png")
    for f in os.listdir(image_dir):

        if f.lower().endswith(suffixes):
            yield io.imread(os.path.join(image_dir, f))


if __name__ == "__main__":
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.imshow(next(get_images()))
    ax.set_axis_off()
    plt.show()
