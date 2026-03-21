import skimage as ski
import matplotlib.pyplot as plt
from skimage.color import rgb2gray
from skimage import color, feature, io, measure
import os
from scipy import ndimage as ndi
import numpy as np
from RegionSegmentation import get_region_segmentation


def process_image(image):

    regionregionprops = get_region_segmentation(image, show=False)

    mean_region_area = np.mean([region.area for region in regionregionprops])
    num_cells = len(regionregionprops)
    total_region_area = np.sum([region.area for region in regionregionprops])

    return regionregionprops, [focus_laplacian(image), mean_pixel_val(image), mean_region_area, num_cells, total_region_area]


# inputs grayscale image; returns 0 (least blurry) to 1 (most blurry); group id
def blur(image):
    return ski.measure.blur_effect(image + 1e-6, channel_axis=None)

def focus_laplacian(image):
    lap = ski.filters.laplace(image)
    return lap.var()

# inputs grayscale image; returns mean pixel value
def mean_pixel_val(image):
    return np.mean(image)

def process_object(segment):
    return [segment.eccentricity, segment.area, segment.perimeter]
