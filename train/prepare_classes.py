import os
import argparse

def extract_class_names(data_dir, output_file='class_names.txt'):
    """
    Extract class names from the data directory and save to a file.
    
    Args:
        data_dir: Directory containing class subfolders
        output_file: File to save class names
    """
    # Get all directory names and sort them
    class_names = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    class_names.sort()
    
    # Print found classes
    print(f"Found {len(class_names)} classes:")
    for cls in class_names:
        print(f"  - {cls}")
    
    # Save to file
    with open(output_file, 'w') as f:
        for cls in class_names:
            f.write(f"{cls}\n")
    
    print(f"Class names saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Prepare class names from data directory")
    parser.add_argument('--data_dir', type=str, required=True, help='Directory with class folders')
    parser.add_argument('--output', type=str, default='class_names.txt', help='Output file for class names')
    
    args = parser.parse_args()
    extract_class_names(args.data_dir, args.output)

if __name__ == "__main__":
    main()