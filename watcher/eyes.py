import cv2
import numpy as np
import mss
import pyautogui
import pygetwindow as gw
import time
import tkinter as tk
import random

# --- CONFIGURATION ---
# Adjust these values to change the area to watch on the screen.
# (top, left) are the coordinates of the top-left corner.
WATCH_REGION = {'top': 700, 'left': 50, 'width': 50, 'height': 400}

# List of your template images to search for.
# Make sure these files are in the same directory as the script.
TEMPLATE_IMAGES = [
    'neutral.png',
    'neutral2.png',
    'bad.png',
    'terrible.png'
]

# The title of the window to activate when a match is found.
# Use a unique part of the window title for EVE Online.
TARGET_WINDOW_TITLE = "EVE - Vemor Phose" 

# Confidence threshold for matching. A value between 0.0 and 1.0.
# 0.8 (80%) is a good starting point.
CONFIDENCE_THRESHOLD = 0.8

# Time to wait between each scan in seconds.
LOOP_DELAY = 0.5
# --- END OF CONFIGURATION ---

def create_overlay_box(region):
    """Creates a transparent window with a green border to show the watched area."""
    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry(f"{region['width']}x{region['height']}+{region['left']}+{region['top']}")
    root.wm_attributes("-topmost", True)
    root.wm_attributes("-transparentcolor", "white")
    root.config(bg='white')
    
    canvas = tk.Canvas(root, bg='white', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    canvas.create_rectangle(
        2, 2, region['width']-2, region['height']-2, 
        outline='lime', width=3
    )
    return root

def perform_macro():
    """
    This is where you define your macro actions.
    This function is called AFTER the EVE Online window is activated.
    """
    print(">>> Performing pre-defined macro...")
    
    # 1. Wait 1 second (+ random delay) after the window is activated.
    time.sleep(1 + random.uniform(0, 0.25))
    
    # 2. Click once in the exact centre of the screen (2160 x 1600).
    print("Clicking center of screen at (1080, 800)...")
    pyautogui.moveTo(1080, 800)
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()
    
    # 3. Wait 1 second (+ random delay).
    time.sleep(1 + random.uniform(0, 0.25))
    
    # 4. Press Left click at a particular pixel.
    left_click_x_1 = 929
    left_click_y_1 = 1380
    print(f"Left-clicking at ({left_click_x_1}, {left_click_y_1})...")
    pyautogui.moveTo(left_click_x_1, left_click_y_1)
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()
    
    # 5. Wait 10 seconds (+ random delay).
    print("Waiting 10 seconds...")
    time.sleep(10 + random.uniform(0, 0.25))
    
    # 6. Right click at a particular pixel.
    right_click_x = 94
    right_click_y = 1014
    print(f"Right-clicking at ({right_click_x}, {right_click_y})...")
    pyautogui.moveTo(right_click_x, right_click_y)
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.rightClick()
    
    # 7. Wait 1 second (+ random delay).
    time.sleep(1 + random.uniform(0, 0.25))
    
    # 8. Left click at a particular pixel.
    left_click_x_2 = 149
    left_click_y_2 = 1094
    print(f"Left-clicking at ({left_click_x_2}, {left_click_y_2})...")
    pyautogui.moveTo(left_click_x_2, left_click_y_2)
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()
    
    # 9. Wait 1 second (+ random delay) before the script terminates.
    time.sleep(1 + random.uniform(0, 0.25))
    
    print(">>> Macro finished.")


def main():
    """Main function to run the detection loop."""
    print("--- Starting Screen Detector ---")
    print(f"Watching region: {WATCH_REGION}")

    try:
        templates = [cv2.imread(img, cv2.IMREAD_GRAYSCALE) for img in TEMPLATE_IMAGES]
        if any(t is None for t in templates):
            print("Error: One or more template images could not be loaded.")
            print("Please ensure the image files are in the correct directory and are not corrupted.")
            return
    except Exception as e:
        print(f"An error occurred while loading images: {e}")
        return

    overlay = create_overlay_box(WATCH_REGION)
    
    sct = mss.mss()

    try:
        while True:
            overlay.update()
            
            screenshot = sct.grab(WATCH_REGION)
            img = np.array(screenshot)
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)

            for i, template in enumerate(templates):
                if template is None: continue # Skip if a template failed to load

                res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)

                if max_val >= CONFIDENCE_THRESHOLD:
                    print(f"SUCCESS: Match found for '{TEMPLATE_IMAGES[i]}' with {max_val*100:.2f}% confidence.")
                    
                    try:
                        eve_windows = gw.getWindowsWithTitle(TARGET_WINDOW_TITLE)
                        if eve_windows:
                            print(f"Activating window: {eve_windows[0].title}")
                            eve_windows[0].activate()
                            time.sleep(0.5)
                        else:
                            print(f"Error: Could not find a window with title containing '{TARGET_WINDOW_TITLE}'.")
                            print("Script will now terminate.")
                            return

                    except Exception as e:
                        print(f"An error occurred while activating the window: {e}")
                        return

                    perform_macro()
                    
                    print("--- Script finished successfully. ---")
                    return

            time.sleep(LOOP_DELAY)

    except KeyboardInterrupt:
        print("\n--- Script stopped by user. ---")
    finally:
        overlay.destroy()


if __name__ == "__main__":
    main()

