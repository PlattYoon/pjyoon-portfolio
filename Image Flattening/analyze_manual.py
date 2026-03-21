import numpy as np
import matplotlib.pyplot as plt
from skimage import io, color, measure, morphology
from scipy import ndimage as ndi

vishakha_labelled = io.imread(r'./labelled_images/Vishakha_circles.jpg')
paul_labelled = io.imread(r'./labelled_images/Paul_circles.jpg')
justin_labelled = io.imread(r'./labelled_images/Justin_circles.jpg')

def labelled_images_to_regions(images, show=False):

    images = [vishakha_labelled, paul_labelled, justin_labelled]


    red_color = np.array([255, 0, 0])

    tolerance = 100
    red_masks = [np.all(np.abs(image - red_color) <= tolerance, axis=-1) for image in images]

    filled_masks = [ndi.binary_fill_holes(red_mask) for red_mask in red_masks]

    if show:
        names = ["Vishakha's plate", "Paul's plate", "Justin's plate"]
        for i, filled_mask in enumerate(filled_masks):
            fig, ax = plt.subplots(figsize=(4, 3))
            ax.imshow(filled_mask, cmap=plt.cm.gray)
            ax.set_title(f"Manual Segmentation Result for \n{names[i]}")
            ax.set_axis_off()
            plt.show()

    labels = [measure.label(filled_mask) for filled_mask in filled_masks]
    regionprops = [measure.regionprops(label) for label in labels]
    return regionprops

def regions_to_average_area(regions):
    return np.mean([region.area for region in regions])

def regions_to_region_count(regions):
    return len(regions)


if __name__ == "__main__":
    labelled_images_to_regions(None, show=True)


