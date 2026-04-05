
import sys

def read_file(filename):
    encodings = ['utf-16le', 'utf-8', 'cp1252']
    for enc in encodings:
        try:
            with open(filename, 'r', encoding=enc) as f:
                content = f.read()
                print(f"--- Content decoded with {enc} ---")
                print(content)
                return
        except Exception:
            continue
    print("Failed to decode file with standard encodings.")

read_file('build_log_attempt_2.txt')
