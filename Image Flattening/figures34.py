import numpy as np
from analyze_manual import *
from RegionSegmentation import *
from EdgeSegmentation import *

baseline = labelled_images_to_regions(None)

region = get_region_segmentation(show=False)

edge = get_edge_segmentation(show=False)

Vishakha = [baseline[0], region[2], edge[2]]
Paul = [baseline[1], region[0], edge[0]]
Justin = [baseline[2], region[1], edge[1]]

vishakha_area = list(map(regions_to_average_area, Vishakha))
paul_area = list(map(regions_to_average_area, Paul))
justin_area = list(map(regions_to_average_area, Justin))

vishakha_count = list(map(regions_to_region_count, Vishakha))
paul_count = list(map(regions_to_region_count, Paul))
justin_count = list(map(regions_to_region_count, Justin))


image_labels = ["Vishakha", "Paul", "Justin"]

method_labels = ["Baseline", "Watershed", "Edge Segmentation"]

area_data = np.array([
    vishakha_area,  # [baseline, watershed, edge]
    paul_area,
    justin_area
])

count_data = np.array([
    vishakha_count,
    paul_count,
    justin_count
])

# Parameters
n_images = len(image_labels)
n_methods = len(method_labels)
bar_width = 0.25
x = np.arange(n_images)  # group positions

# Plot
fig, ax = plt.subplots(figsize=(10, 6))

for i in range(n_methods):
    ax.bar(x + i * bar_width, area_data[:, i], width=bar_width, label=method_labels[i])

# Formatting
ax.set_xlabel('Image')
ax.set_ylabel('Average Area')
ax.set_title('Average Area per Method for Each Image')
ax.set_xticks(x + bar_width)  # Center the groups
ax.set_xticklabels(image_labels)
ax.legend()

plt.tight_layout()
plt.show()


fig, ax = plt.subplots(figsize=(10, 6))
for i in range(n_methods):
    ax.bar(x + i * bar_width, count_data[:, i], width=bar_width, label=method_labels[i])

ax.set_xlabel('Image')
ax.set_ylabel('Region Count')
ax.set_title('Region Count per Method for Each Image')
ax.set_xticks(x + bar_width)
ax.set_xticklabels(image_labels)
ax.legend()

plt.tight_layout()
plt.show()

