import cv2

# Declaring program constants
HIGHEST_ZL = 23
MIN_LATITUDE = -85.05112878
MAX_LATITUDE = 85.05112878
MIN_LONGITUDE = -180
MAX_LONGITUDE = 180



# This is a custom function that returns the minimum of maximum of first two inputs and the third input
def clip(n, minVal, maxVal):
	return min(max(n,minVal),maxVal)



# This function does basic image resizing with either height or width input
def resize_img(img, width = None, height = None, inter = cv2.INTER_AREA):
	# Set up the image dimensions to be resized and get size of the image
	dim = None
	(hght, wdth) = img.shape[:2]

	# Return original image if input dimensions are None, else calculate new dimensions
	if width is None and height is None:
		return img

	if width is None:
		# Derive height ratio to construct new dimensions
		ratio = height / float(hght)
		newdim = (int(wdth * ratio), height)
	else:
		# Derive width ratio to construct new dimensions
		ratio = width / float(wdth)
		newdim = (width, int(hght * ratio))

	# Resize and return image
	resized = cv2.resize(img, newdim, interpolation = inter)
	return resized



