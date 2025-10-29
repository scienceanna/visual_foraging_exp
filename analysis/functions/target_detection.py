
# This module is used to load images
from PIL import Image
# This module contains a number of arithmetical image operations
from PIL import ImageChops, ImageFilter

import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt


img=Image.open('C:/Users/ah19679/Documents/GitHub/visual_foraging_exp/data/leberlab/1_block0_exhaustive_0.png')
img_bg = Image.open('C:/Users/ah19679/Documents/GitHub/visual_foraging_exp/data/leberlab/1_block0_exhaustive_0_background.png')
# compare my images?
diff = ImageChops.difference(img_bg, img)

# set a threshold to make a mask
threshold = 1

diff_threshold = diff.point(
    lambda x: 255 if x > threshold else 0
)

# try dilating & eroding
def dilate(cycles, image):
    for _ in range(cycles):
        image = image.filter(ImageFilter.MaxFilter(3))
    return image

def erode(cycles, image):
    for _ in range(cycles):
        image = image.filter(ImageFilter.MinFilter(3))
    return image

diff_dilate = dilate(6,diff_threshold)
diff_erode = erode(4, diff_dilate)

# making a mask
diff_mask = diff_erode.convert("L")

blank = img.point(lambda _: 0)
img_segmented = Image.composite(img, blank, diff_mask)
img_segmented.show()

# trying to label contours?
# borrowing liberally from https://gist.github.com/digitalspecialists/3c0221af7b1fba42325401e269920d67
I = np.asarray(img_segmented)
I2 = cv.cvtColor(I, cv.COLOR_BGR2GRAY)
contours, _ = cv.findContours(I2, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
canvas = np.zeros(I.shape[:2])

for i, contour in enumerate(contours[0:]):
    this_letter = np.zeros(I.shape[:2], np.uint8)
    cv.drawContours(this_letter, [contour], -1, (255), -1)
    mean_masked, stdev_masked = cv.meanStdDev(I2, mask = this_letter)
    loc, dims, angle = cv.minAreaRect(contour) # unused, but useful to crop

    print(f'Letter #{i}', \
              ' location ', "{:.0f}".format(loc[0]), "{:.0f}".format(loc[1]), \
              ' mean gray', "{:.2f}".format(float(mean_masked[0])), \
              ' std', "{:.2f}". format(float(stdev_masked[0])))
    
    cv.drawContours(canvas, [contour], -1, (255), -1)

plt.figure(figsize=(12,12))
plt.imshow(canvas)
plt.show()
