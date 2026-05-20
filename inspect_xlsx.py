import os
import glob

def check_xlsx():
    files = glob.glob("/Users/dallas_work/Downloads/*.xlsx")
    print("Found XLSX files:")
    for f in files:
        size = os.path.getsize(f)
        print(f"  - {os.path.basename(f)} ({size} bytes)")
        
if __name__ == "__main__":
    check_xlsx()
