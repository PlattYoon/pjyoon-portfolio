import numpy as np
import skimage as ski
import matplotlib.pyplot as plt
from skimage.color import rgb2gray
from skimage import color, feature, io, measure, filters, morphology
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

        fig, axes = plt.subplots(1, 2, figsize=(10, 5))
        
        ax = axes[0]
        ax.imshow(image, cmap='gray')
        ax.set_title('Original Image')
        ax.axis('off')

        ax = axes[1]
        ax.imshow(image_cleaned, cmap='gray')
        ax.set_title('Segmented (Adaptive Threshold)')
        ax.axis('off')

        plt.tight_layout()
        plt.show()


        #fig, ax = plt.subplots(figsize=(4, 3))
        #ax.imshow(edges, cmap=plt.cm.gray)
        #ax.set_title(f'Highlighted Edges for {fname}')
        #ax.set_axis_off()

        #plt.show()

    labeled_mask = measure.label(image_cleaned)
    props = measure.regionprops(labeled_mask)
    return props

    """
    # Convert to grayscale
    if image.ndim == 3:
        gray = color.rgb2gray(image)
    else:
        gray = image

    # Apply adaptive (local) thresholding
    window_size = 91  # Can be tuned
    thresh_sauvola = filters.threshold_sauvola(gray, window_size=window_size)
    binary_mask = gray < thresh_sauvola  # or < if cells are darker

    # Morphological cleaning
    cleaned = morphology.remove_small_objects(binary_mask, min_size=50)
    cleaned = morphology.binary_closing(cleaned, morphology.disk(2))

    # Label connected components
    labeled = measure.label(cleaned)
    props = measure.regionprops(labeled)

    if show:
        fig, axes = plt.subplots(1, 2, figsize=(10, 5))
        
        ax = axes[0]
        ax.imshow(image, cmap='gray')
        ax.set_title('Original Image')
        ax.axis('off')

        ax = axes[1]
        ax.imshow(cleaned, cmap='gray')
        ax.set_title('Segmented (Adaptive Threshold)')
        ax.axis('off')

        plt.tight_layout()
        plt.show()

    return props
    """
