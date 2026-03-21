import skimage as ski
import matplotlib.pyplot as plt
from skimage.color import rgb2gray
from skimage import color, feature, io, measure
import os
from scipy import ndimage as ndi


def get_edge_segmentation(image, show=False):
    """
    Takes in a skimage image. Outputs a skimage regionprops. To read in images, check out load_images.py
    """
    # Convert to grayscale
    if image.ndim == 3:  
        # Drop alpha if RGBA
        if image.shape[2] == 4:
            image = image[:, :, :3]
        gray = color.rgb2gray(image)
    else:
        gray = image

    # Run Canny edge detection
    edges = feature.canny(gray, sigma=1.5)
    fill_image = ndi.binary_fill_holes(edges)   
    image_cleaned = ski.morphology.remove_small_objects(fill_image, 21)

    if show:
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.imshow(image_cleaned, cmap=plt.cm.gray)
        ax.set_title(f'Edge Segmentation Result for {fname}')
        ax.set_axis_off()
        plt.show()


        #fig, ax = plt.subplots(figsize=(4, 3))
        #ax.imshow(edges, cmap=plt.cm.gray)
        #ax.set_title(f'Highlighted Edges for {fname}')
        #ax.set_axis_off()

        #plt.show()

    labeled_mask = measure.label(image_cleaned)
    props = measure.regionprops(labeled_mask)
    return props


