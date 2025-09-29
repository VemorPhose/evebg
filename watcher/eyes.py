import cv2
import numpy as np
import mss
import pyautogui
import pygetwindow as gw
import time
import tkinter as tk
import random

# --- PRIMARY CHECK CONFIGURATION ---
WATCH_REGION = {'top': 700, 'left': 50, 'width': 50, 'height': 400}
TEMPLATE_IMAGES = [
    'neutral.png',
    'neutral2.png',
    'bad.png',
    'terrible.png'
]
TARGET_WINDOW_TITLE = "EVE - Vemor Phose" 
CONFIDENCE_THRESHOLD = 0.8
# --- END OF PRIMARY CHECK CONFIGURATION ---


# --- SECONDARY CHECK CONFIGURATION ---
# Define the second area to watch on the screen.
WATCH_REGION_2 = {'top': 100, 'left': 1000, 'width': 200, 'height': 100}
# List of template images for the second check.
TEMPLATE_IMAGES_2 = ['secondary_image.png']
# Confidence threshold for the second check.
CONFIDENCE_THRESHOLD_2 = 0.8
# --- END OF SECONDARY CHECK CONFIGURATION ---


# Time to wait between each full scan cycle in seconds.
LOOP_DELAY = 0.5


def create_overlay_box(region, color):
    """Creates a transparent window with a colored border to show the watched area."""
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
        outline=color, width=3
    )
    return root

def perform_macro():
    """
    This is the macro for the PRIMARY check (green box).
    This function is called AFTER the EVE Online window is activated.
    """
    print(">>> Performing PRIMARY pre-defined macro...")
    
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
    time.sleep(15 + random.uniform(0, 0.25))
    
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
    
    print(">>> PRIMARY Macro finished.")

def perform_macro_2():
    """
    This is the macro for the SECONDARY check (blue box).
    This function is called AFTER the EVE Online window is activated.
    """
    print(">>> Performing SECONDARY macro...")
    
    # --- EXAMPLE MACRO ---
    # Replace this with your own sequence of actions for the second trigger.
    pyautogui.press('f2')
    time.sleep(1 + random.uniform(0, 0.25))
    print("Clicking something else at (1500, 800)...")
    pyautogui.moveTo(1500, 800)
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()

    print(">>> SECONDARY Macro finished.")


def main():
    """Main function to run the detection loop."""
    print("--- Starting Screen Detector ---")
    print(f"Watching primary region: {WATCH_REGION}")
    print(f"Watching secondary region: {WATCH_REGION_2}")

    try:
        # Load templates for both checks
        templates1 = [cv2.imread(img, cv2.IMREAD_GRAYSCALE) for img in TEMPLATE_IMAGES]
        templates2 = [cv2.imread(img, cv2.IMREAD_GRAYSCALE) for img in TEMPLATE_IMAGES_2]
        if any(t is None for t in templates1) or any(t is None for t in templates2):
            print("Error: One or more template images could not be loaded.")
            print("Please ensure image files are in the correct directory and not corrupted.")
            return
    except Exception as e:
        print(f"An error occurred while loading images: {e}")
        return

    # Create visual overlays
    overlay1 = create_overlay_box(WATCH_REGION, 'lime') # Green for first check
    overlay2 = create_overlay_box(WATCH_REGION_2, 'blue') # Blue for second check
    
    sct = mss.mss()
    
    # Flag for the secondary check logic. Initialized to True (1).
    secondary_check_flag = True

    try:
        while True:
            # Keep overlay windows responsive
            overlay1.update()
            overlay2.update()
            
            # --- PERFORM FIRST CHECK (GREEN BOX) ---
            screenshot1 = sct.grab(WATCH_REGION)
            img1 = np.array(screenshot1)
            img_gray1 = cv2.cvtColor(img1, cv2.COLOR_BGRA2GRAY)

            for i, template in enumerate(templates1):
                res = cv2.matchTemplate(img_gray1, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)

                if max_val >= CONFIDENCE_THRESHOLD:
                    print(f"SUCCESS (Primary): Match found for '{TEMPLATE_IMAGES[i]}' with {max_val*100:.2f}% confidence.")
                    
                    try:
                        eve_windows = gw.getWindowsWithTitle(TARGET_WINDOW_TITLE)
                        if eve_windows:
                            print(f"Activating window: {eve_windows[0].title}")
                            eve_windows[0].activate()
                            time.sleep(0.5)
                        else:
                            print(f"Error: Could not find window '{TARGET_WINDOW_TITLE}'.")
                            return
                    except Exception as e:
                        print(f"An error occurred while activating window: {e}")
                        return

                    perform_macro()
                    print("--- Script finished successfully. ---")
                    return

            # --- PERFORM SECOND CHECK (BLUE BOX) ---
            screenshot2 = sct.grab(WATCH_REGION_2)
            img2 = np.array(screenshot2)
            img_gray2 = cv2.cvtColor(img2, cv2.COLOR_BGRA2GRAY)
            
            match_found_secondary = False
            matched_image_name = ""
            for i, template in enumerate(templates2):
                res = cv2.matchTemplate(img_gray2, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)

                if max_val >= CONFIDENCE_THRESHOLD_2:
                    match_found_secondary = True
                    matched_image_name = TEMPLATE_IMAGES_2[i]
                    break # A match was found, no need to check other templates

            # Apply the new flag-based logic
            if match_found_secondary and not secondary_check_flag:
                # CONDITION: Image is detected AND flag is 0 -> TRIGGER MACRO
                print(f"SUCCESS (Secondary Trigger): Match for '{matched_image_name}' reappeared.")
                try:
                    eve_windows = gw.getWindowsWithTitle(TARGET_WINDOW_TITLE)
                    if eve_windows:
                        print(f"Activating window: {eve_windows[0].title}")
                        eve_windows[0].activate()
                        time.sleep(0.5)
                    else:
                        print(f"Error: Could not find window '{TARGET_WINDOW_TITLE}'.")
                        return
                except Exception as e:
                    print(f"An error occurred while activating window: {e}")
                    return

                perform_macro_2()
                print("--- Script finished successfully. ---")
                return # Terminate the script after the macro runs
            
            elif not match_found_secondary and secondary_check_flag:
                # CONDITION: Image is NOT detected AND flag is 1 -> Toggle flag to 0
                print("Secondary check: Image has disappeared. Setting flag to 0.")
                secondary_check_flag = False
            
            # The other two conditions (image present & flag=1; image absent & flag=0) require no action.

            # Wait before the next full scan cycle
            time.sleep(LOOP_DELAY)

    except KeyboardInterrupt:
        print("\n--- Script stopped by user. ---")
    finally:
        # Ensure both overlay windows are closed
        overlay1.destroy()
        overlay2.destroy()


if __name__ == "__main__":
    main()


