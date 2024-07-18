import cv2
import numpy as np

def on_trackbar(val):
    pass

# Set the correct file path
file_path = "./test.jpg"
image = cv2.imread(file_path)

# Check if the image was successfully loaded
if image is None:
    print(f"Error: Could not open or find the image '{file_path}'. Please check the file path and try again.")
    exit()

# Create a window
cv2.namedWindow('Threshold')

# Create trackbars
cv2.createTrackbar('Hue Min', 'Threshold', 0, 255, on_trackbar)
cv2.createTrackbar('Hue Max', 'Threshold', 255, 255, on_trackbar)
cv2.createTrackbar('Saturation Min', 'Threshold', 0, 255, on_trackbar)
cv2.createTrackbar('Saturation Max', 'Threshold', 255, 255, on_trackbar)
cv2.createTrackbar('Value Min', 'Threshold', 0, 255, on_trackbar)
cv2.createTrackbar('Value Max', 'Threshold', 255, 255, on_trackbar)

while True:
    # Get the trackbar positions
    hue_min = cv2.getTrackbarPos('Hue Min', 'Threshold')
    hue_max = cv2.getTrackbarPos('Hue Max', 'Threshold')
    saturation_min = cv2.getTrackbarPos('Saturation Min', 'Threshold')
    saturation_max = cv2.getTrackbarPos('Saturation Max', 'Threshold')
    value_min = cv2.getTrackbarPos('Value Min', 'Threshold')
    value_max = cv2.getTrackbarPos('Value Max', 'Threshold')

    # Convert the image to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Create a mask based on the trackbar values
    mask = cv2.inRange(hsv, (hue_min, saturation_min, value_min), (hue_max, saturation_max, value_max))

    # Show the original image and the thresholded image
    cv2.imshow('Original', image)
    cv2.imshow('Thresholded', mask)

    # Exit the loop when the ESC key is pressed
    if cv2.waitKey(1) == 27:
        break

# Destroy all windows
cv2.destroyAllWindows()
