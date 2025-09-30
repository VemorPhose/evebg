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


# --- SECONDARY CHECK CONFIGURATION (TIMED) ---
# The script will run the secondary macro after this many seconds.
# 30 minutes = 30 * 60 = 1800 seconds
MACRO_2_INTERVAL = 2100 
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
    This is the macro for the SECONDARY (timed) check.
    This function is called AFTER the EVE Online window is activated.
    """
    print(">>> Performing SECONDARY macro...")
    
    # --- Tunable Variables for Macro 2 ---
    # The long wait duration in seconds.
    long_wait_duration = 60
    
    # Coordinates for the clicks.
    click_1_coords = {'x': 929, 'y': 1380}
    click_2_coords = {'x': 841, 'y': 116}
    click_3_coords = {'x': 930, 'y': 1171}
    # --- End of Tunable Variables ---

    # 1. Wait 2 seconds (+ random delay) after switching tabs.
    time.sleep(2 + random.uniform(0, 0.25))

    # 2. Left click the first coordinate.
    print(f"Left-clicking first coordinate at ({click_1_coords['x']}, {click_1_coords['y']})...")
    pyautogui.moveTo(click_1_coords['x'], click_1_coords['y'])
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()

    # 3. Wait 2 seconds (+ random delay).
    time.sleep(2 + random.uniform(0, 0.25))

    # 4. Left click the second coordinate.
    print(f"Left-clicking second coordinate at ({click_2_coords['x']}, {click_2_coords['y']})...")
    pyautogui.moveTo(click_2_coords['x'], click_2_coords['y'])
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()
    
    # 5. Wait for the long duration (+ random delay).
    print(f"Waiting for {long_wait_duration} seconds...")
    time.sleep(long_wait_duration + random.uniform(0, 0.25))

    # 6. Left click the third coordinate.
    print(f"Left-clicking third coordinate at ({click_3_coords['x']}, {click_3_coords['y']})...")
    pyautogui.moveTo(click_3_coords['x'], click_3_coords['y'])
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()

    print(">>> SECONDARY Macro finished.")


def main():
    """Main function to run the detection loop."""
    print("--- Starting Screen Detector ---")
    print(f"Watching primary region: {WATCH_REGION}")
    print(f"Secondary macro will run every {MACRO_2_INTERVAL / 60} minutes.")

    try:
        # Load templates for the primary check in color
        templates1 = [cv2.imread(img) for img in TEMPLATE_IMAGES]
        if any(t is None for t in templates1):
            print("Error: One or more template images could not be loaded.")
            print("Please ensure image files are in the correct directory and not corrupted.")
            return
    except Exception as e:
        print(f"An error occurred while loading images: {e}")
        return

    # Create visual overlay for the primary check
    overlay1 = create_overlay_box(WATCH_REGION, 'lime') # Green for first check
    
    sct = mss.mss()
    
    # Initialize the timer for the secondary macro
    last_macro_2_time = time.time()

    try:
        while True:
            # Keep overlay window responsive
            overlay1.update()
            
            # --- PERFORM FIRST CHECK (GREEN BOX) ---
            screenshot1 = sct.grab(WATCH_REGION)
            img1 = np.array(screenshot1)
            # Convert the screenshot from BGRA to BGR for color matching
            img_color1 = cv2.cvtColor(img1, cv2.COLOR_BGRA2BGR)

            for i, template in enumerate(templates1):
                res = cv2.matchTemplate(img_color1, template, cv2.TM_CCOEFF_NORMED)
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

            # --- PERFORM TIMED CHECK (MACRO 2) ---
            if time.time() - last_macro_2_time >= MACRO_2_INTERVAL:
                print(f"Timer reached. Triggering secondary macro...")
                try:
                    eve_windows = gw.getWindowsWithTitle(TARGET_WINDOW_TITLE)
                    if eve_windows:
                        print(f"Activating window: {eve_windows[0].title}")
                        eve_windows[0].activate()
                        time.sleep(0.5)
                    else:
                        print(f"Error: Could not find window '{TARGET_WINDOW_TITLE}' for secondary macro.")
                        # Continue the loop even if window not found, maybe it will reappear
                        continue 
                except Exception as e:
                    print(f"An error occurred while activating window for secondary macro: {e}")
                    continue

                perform_macro_2()
                print("Resetting timer for secondary macro.")
                # Reset the timer for the next interval
                last_macro_2_time = time.time()

            # Wait before the next full scan cycle
            time.sleep(LOOP_DELAY)

    except KeyboardInterrupt:
        print("\n--- Script stopped by user. ---")
    finally:
        # Ensure the overlay window is closed
        overlay1.destroy()


if __name__ == "__main__":
    main()
