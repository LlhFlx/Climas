import os
import sys

def count_lines_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for line in f)
    except (UnicodeDecodeError, PermissionError, FileNotFoundError):
        # Skip files that can't be read as text
        return 0

def count_lines_recursive(root_dir):
    total_lines = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            lines = count_lines_in_file(filepath)
            total_lines += lines
            # Optional: print per-file count
            print(f"{filepath}: {lines} lines")
    return total_lines

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 myscript.py <folder_path>")
        sys.exit(1)

    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a valid directory.")
        sys.exit(1)

    total = count_lines_recursive(folder)
    print(f"Total of {total} lines.")