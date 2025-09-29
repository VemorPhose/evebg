import pyautogui
import time

print("Starting mouse coordinate finder...")
print("Press Ctrl+C to stop the script.")

try:
    while True:
        # Get the current mouse coordinates.
        x, y = pyautogui.position()
        
        # Format the position string.
        # The ' ' padding ensures the previous line is overwritten completely.
        position_str = f"X: {x:4d}, Y: {y:4d}"
        
        # Print the coordinates, overwriting the previous line.
        # The `end='\r'` moves the cursor to the beginning of the line.
        # `flush=True` ensures it prints immediately.
        print(position_str, end='\r', flush=True)
        
        # Wait a short moment to reduce CPU usage.
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nScript stopped.")
