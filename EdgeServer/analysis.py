import cv2
import numpy as np

def get_relative_size(bbox, img_width, img_height):
    """
    Calculates the percentage of the screen the object occupies.
    bbox: [x1, y1, x2, y2]
    """
    x1, y1, x2, y2 = bbox
    obj_width = x2 - x1
    obj_height = y2 - y1
    
    obj_area = obj_width * obj_height
    total_area = img_width * img_height
    
    percentage = (obj_area / total_area) * 100
    return round(percentage, 2)

def get_dominant_color(img_crop):
    """
    Estimates the dominant color name of the object.
    img_crop: The cropped image of the object (BGR format from OpenCV)
    """
    if img_crop.size == 0:
        return "Unknown"

    # 1. Resize to small size to speed up processing
    resized = cv2.resize(img_crop, (64, 64), interpolation=cv2.INTER_AREA)
    
    # 2. Calculate average color of the center (to avoid background noise)
    # We take the center 50% of the crop
    h, w, _ = resized.shape
    center_crop = resized[int(h*0.25):int(h*0.75), int(w*0.25):int(w*0.75)]
    avg_color_per_row = np.average(center_crop, axis=0)
    avg_color = np.average(avg_color_per_row, axis=0) # Returns [B, G, R]

    # 3. Define standard colors (BGR format)
    colors = {
        "Red": (0, 0, 255),
        "Green": (0, 255, 0),
        "Blue": (255, 0, 0),
        "Black": (0, 0, 0),
        "White": (255, 255, 255),
        "Gray": (128, 128, 128),
        "Yellow": (0, 255, 255),
        "Orange": (0, 165, 255),
        "Purple": (128, 0, 128)
    }

    # 4. Find the closest color using Euclidean distance
    min_dist = float("inf")
    closest_name = "Unknown"
    
    for name, rgb in colors.items():
        # Calculate distance: sqrt((b1-b2)^2 + (g1-g2)^2 + (r1-r2)^2)
        dist = np.linalg.norm(avg_color - np.array(rgb))
        if dist < min_dist:
            min_dist = dist
            closest_name = name

    return closest_name