import skimage as ski
import matplotlib.pyplot as plt
from skimage.color import rgb2gray
from skimage import color, feature, io, measure
import os
from scipy import ndimage as ndi
import numpy as np

# inputs grayscale image; returns 0 (least blurry) to 1 (most blurry); group id
def blur(image):
    return ski.measure.blur_effect(image, channel_axis=None)

# inputs grayscale image; returns mean pixel value
def mean_pixel_val(image):
    return np.mean(image)
