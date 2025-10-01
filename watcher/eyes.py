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

# --- SECONDARY CHECK CONFIGURATION ---
# The time in seconds between running the secondary macro.
MACRO_2_INTERVAL = 38 * 60 # 38 minutes

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

def blink_warning_box(screen_width, screen_height):
    """Creates and blinks a yellow warning box in the center of the screen."""
    print("...Blinking warning for upcoming macro...")
    warn_root = tk.Tk()
    warn_root.overrideredirect(True)
    box_size = 100
    # Calculate center position
    pos_x = (screen_width // 2) - (box_size // 2)
    pos_y = (screen_height // 2) - (box_size // 2)
    warn_root.geometry(f"{box_size}x{box_size}+{pos_x}+{pos_y}")
    warn_root.wm_attributes("-topmost", True)
    warn_root.config(bg='yellow')
    
    # Hide it initially
    warn_root.withdraw()
    warn_root.update()

    # Blink loop
    for _ in range(5):
        warn_root.deiconify() # Show
        warn_root.update()
        time.sleep(0.5)
        warn_root.withdraw() # Hide
        warn_root.update()
        time.sleep(0.5)
        
    warn_root.destroy()

def perform_macro():
    """
    This is where you define your macro actions.
    This function is called AFTER the EVE Online window is activated.
    """
    print(">>> Performing pre-defined macro...")
    
    # 1. Wait 1 second after the window is activated.
    time.sleep(1 + random.uniform(0, 0.25))
    
    # 2. Click once in the exact centre of the screen (2160 x 1600).
    #    Center coordinates are (2160 / 2, 1600 / 2) = (1080, 800)
    print("Clicking center of screen at (1080, 800)...")
    pyautogui.moveTo(1080, 800)
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()
    
    # 3. Wait 1 second.
    time.sleep(1 + random.uniform(0, 0.25))
    
    # 4. Press Left click at a particular pixel.
    left_click_x_1 = 929
    left_click_y_1 = 1380
    print(f"Left-clicking at ({left_click_x_1}, {left_click_y_1})...")
    pyautogui.moveTo(left_click_x_1, left_click_y_1)
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()
    
    # 5. Wait 10 seconds.
    print("Waiting 10 seconds...")
    time.sleep(10 + random.uniform(0, 0.25))
    
    # 6. Right click at a particular pixel.
    right_click_x = 94
    right_click_y = 1014
    print(f"Right-clicking at ({right_click_x}, {right_click_y})...")
    pyautogui.moveTo(right_click_x, right_click_y)
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.rightClick()
    
    # 7. Wait 1 second.
    time.sleep(1 + random.uniform(0, 0.25))
    
    # 8. Left click at a particular pixel.
    left_click_x_2 = 149
    left_click_y_2 = 1094
    print(f"Left-clicking at ({left_click_x_2}, {left_click_y_2})...")
    pyautogui.moveTo(left_click_x_2, left_click_y_2)
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()
    
    # 9. Wait 1 second before the script terminates.
    time.sleep(1 + random.uniform(0, 0.25))
    
    print(">>> Macro finished.")


def perform_macro_2():
    """
    This is the macro for the SECONDARY (timed) check.
    This function is called AFTER the EVE Online window is activated.
    """
    print(">>> Performing SECONDARY macro...")
    
    # --- Tunable Variables for Macro 2 ---
    # Coordinates for the clicks.
    click_1_coords = {'x': 929, 'y': 1380}
    click_2_coords = {'x': 841, 'y': 116}
    # !!! TUNE THESE COORDINATES MANUALLY !!!
    click_3_coords = {'x': 1763, 'y': 1475}
    click_4_coords = {'x': 1763, 'y': 1475} 
    # --- End of Tunable Variables ---

    # 1. Wait 2 seconds (+ random delay) after switching tabs.
    time.sleep(2 + random.uniform(0, 0.25))
    
    # 2. Left click coordinate 1.
    print(f"Left-clicking at ({click_1_coords['x']}, {click_1_coords['y']})...")
    pyautogui.moveTo(click_1_coords['x'], click_1_coords['y'])
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()

    # 3. Wait 15 seconds (+ random delay).
    time.sleep(15 + random.uniform(0, 0.25))

    # 4. Left click coordinate 2.
    print(f"Left-clicking at ({click_2_coords['x']}, {click_2_coords['y']})...")
    pyautogui.moveTo(click_2_coords['x'], click_2_coords['y'])
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()

    # 5. Wait 2 seconds (+ random delay).
    print("Waiting 2 seconds...")
    time.sleep(2 + random.uniform(0, 0.25))

    # 6. Left click coordinate 3.
    print(f"Left-clicking at ({click_3_coords['x']}, {click_3_coords['y']})...")
    pyautogui.moveTo(click_3_coords['x'], click_3_coords['y'])
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()

    # 7. Wait 56 seconds (+ random delay).
    print("Waiting 56 seconds...")
    time.sleep(56 + random.uniform(0, 0.25))

    # 8. Left click coordinate 4.
    print(f"Left-clicking at ({click_4_coords['x']}, {click_4_coords['y']})...")
    pyautogui.moveTo(click_4_coords['x'], click_4_coords['y'])
    time.sleep(random.uniform(0.5, 0.75))
    pyautogui.click()
    
    # 9. Wait 2 seconds (+ random delay).
    print("Waiting 2 seconds...")
    time.sleep(2 + random.uniform(0, 0.25))

    print(">>> SECONDARY Macro finished. Returning to loop.")


def main():
    """Main function to run the detection loop."""
    print("--- Starting Screen Detector ---")
    print(f"Watching region: {WATCH_REGION}")
    screen_width, screen_height = pyautogui.size()
    print(f"Screen dimensions: {screen_width}x{screen_height}")

    try:
        templates = [cv2.imread(img, cv2.IMREAD_COLOR) for img in TEMPLATE_IMAGES]
        if any(t is None for t in templates):
            print("Error: One or more template images could not be loaded.")
            print("Please ensure the image files are in the correct directory and are not corrupted.")
            return
    except Exception as e:
        print(f"An error occurred while loading images: {e}")
        return

    overlay = create_overlay_box(WATCH_REGION)
    sct = mss.mss()

    # Timers and flags for the secondary macro
    last_macro_2_time = 0
    first_run_macro_2 = True
    last_log_time = time.time()
    warning_triggered_for_this_interval = False

    try:
        while True:
            overlay.update()
            
            # --- PERFORM PRIMARY IMAGE CHECK (MACRO 1) ---
            screenshot = sct.grab(WATCH_REGION)
            img = np.array(screenshot)
            img_color = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            for i, template in enumerate(templates):
                if template is None: continue
                
                res = cv2.matchTemplate(img_color, template, cv2.TM_CCOEFF_NORMED)
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

            # --- PERIODIC LOGGING ---
            # Log time since last macro 2 run every 5 minutes (300 seconds)
            if time.time() - last_log_time >= 300:
                minutes_passed = (time.time() - last_macro_2_time) / 60 if not first_run_macro_2 else 0
                print(f"[{time.strftime('%H:%M:%S')}] {minutes_passed:.2f} minutes since last secondary macro.")
                last_log_time = time.time()

            # --- PRE-MACRO 2 WARNING ---
            # Check if we are within 15 seconds of the next macro trigger
            if not first_run_macro_2:
                time_until_macro_2 = MACRO_2_INTERVAL - (time.time() - last_macro_2_time)
                if 0 < time_until_macro_2 <= 15 and not warning_triggered_for_this_interval:
                    blink_warning_box(screen_width, screen_height)
                    warning_triggered_for_this_interval = True

            # --- PERFORM TIMED CHECK (MACRO 2) ---
            if first_run_macro_2 or (time.time() - last_macro_2_time >= MACRO_2_INTERVAL):
                if first_run_macro_2:
                    print("Performing initial run of secondary macro...")
                else:
                    print(f"Timer reached. Triggering secondary macro...")
                
                try:
                    eve_windows = gw.getWindowsWithTitle(TARGET_WINDOW_TITLE)
                    if eve_windows:
                        win = eve_windows[0]
                        print(f"Attempting to activate window: {win.title}")
                        
                        # --- MORE ROBUST ACTIVATION LOGIC ---
                        if win.isMinimized:
                            win.restore()
                            time.sleep(0.5)

                        win.activate()
                        time.sleep(0.5)

                        print("Forcing focus with a confirmation click at (0, 1200)...")
                        pyautogui.click(x=0, y=1200) 
                        time.sleep(0.5)
                        # --- END OF MORE ROBUST ACTIVATION LOGIC ---

                    else:
                        print(f"Error: Could not find window '{TARGET_WINDOW_TITLE}' for secondary macro.")
                        continue 
                except Exception as e:
                    print(f"An error occurred while activating window for secondary macro: {e}")
                    print("This can happen if the script lacks admin rights or another app is preventing focus.")
                    continue

                perform_macro_2()
                last_macro_2_time = time.time()
                first_run_macro_2 = False
                warning_triggered_for_this_interval = False # Reset the warning flag
                continue

            time.sleep(LOOP_DELAY)

    except KeyboardInterrupt:
        print("\n--- Script stopped by user. ---")
    finally:
        overlay.destroy()


if __name__ == "__main__":
    main()
