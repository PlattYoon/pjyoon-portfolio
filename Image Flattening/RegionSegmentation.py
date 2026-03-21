import os
import numpy as np
import matplotlib.pyplot as plt
from skimage import io, color, filters, exposure, morphology, segmentation, measure, util

image_dir = r"./Cropped"

# Collect all JPGs in the folder
image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(".png")]

def get_region_segmentation(show=False):

    all_regionprops = []

    for fname in image_files:
        path = os.path.join(image_dir, fname)
        img = io.imread(path)

        # --- 1) Grayscale float in [0,1] (drop alpha if present) ---
        if img.ndim == 3 and img.shape[2] == 4:
            img = img[:, :, :3]
        if img.ndim == 3:
            gray = color.rgb2gray(img)
        else:
            gray = util.img_as_float(img)

        # Optional robustness: local contrast + light denoise
        gray = exposure.equalize_adapthist(gray, clip_limit=0.02)  # CLAHE
        gray = filters.gaussian(gray, sigma=1.0, preserve_range=True)

        # --- 2) Elevation map (just like the coins tutorial) ---
        elevation = filters.sobel(gray)

        # --- 3) Marker seeding (background=1, foreground=2) ---
        # Use robust percentiles rather than raw byte thresholds
        low_t  = np.quantile(gray, 0.35)
        high_t = np.quantile(gray, 0.80)

        markers = np.zeros(gray.shape, dtype=np.int32)   # 2-D!
        markers[gray < low_t]  = 1
        markers[gray > high_t] = 2
        markers = morphology.dilation(markers, morphology.disk(2))  # stabilize seeds

        # --- 4) Watershed ---
        labels = segmentation.watershed(elevation, markers)

        # Keep foreground mask and clean it up
        mask = labels == 2
        mask = morphology.remove_small_objects(mask, min_size=200)
        mask = morphology.remove_small_holes(mask, area_threshold=200)

        # --- 5) Visualize ---
        if show:
            fig, axes = plt.subplots(1, 3, figsize=(12, 4))
            ax = axes.ravel()
            ax[0].imshow(gray, cmap="gray"); ax[0].set_title("grayscale"); ax[0].set_axis_off()
            ax[1].imshow(elevation, cmap="magma"); ax[1].set_title("elevation (sobel)"); ax[1].set_axis_off()
            ax[2].imshow(mask, cmap="gray"); ax[2].set_title(f"watershed mask: {fname}"); ax[2].set_axis_off()
            plt.tight_layout(); plt.show()

        labeled_mask = measure.label(mask)

        props = measure.regionprops(labeled_mask)
        all_regionprops.append(props)
    return all_regionprops
        

if __name__ == "__main__":
    get_region_segmentation(show=True)
