import shutil
import os

source_path = r"C:\Users\virat\.gemini\antigravity\brain\6e298c5b-7666-4c2d-8857-aba9bfd9ad05\traffic_app_icon_1778400609429.png"
dest_path = r"c:\Users\virat\Desktop\traffic\static\logo.png"

try:
    shutil.copyfile(source_path, dest_path)
    print("SUCCESS: The new traffic light logo has been copied to your static folder!")
    print("Please refresh your browser to see it.")
except Exception as e:
    print(f"Error copying file: {e}")
