import os
import re

def rename_files(directory):
    # Dictionary to keep track of file counts
    file_counts = {}

    # Iterate through all files in the directory
    for filename in os.listdir(directory):
        # Remove the word "copy" from the filename
        new_name = re.sub(r'\bcopy\b', '', filename, flags=re.IGNORECASE).strip()
        
        # Replace all spaces with underscores
        new_name = new_name.replace(' ', '_')
        
        # Remove any extra underscores
        new_name = re.sub(r'_+', '_', new_name)
        
        # Split the filename and extension
        name, ext = os.path.splitext(new_name)
        
        # If the filename already exists, add a count
        if new_name in file_counts:
            count = file_counts[new_name] + 1
            new_name = f"{name}_{count}{ext}"
        else:
            count = 0
        
        file_counts[new_name] = count
        
        # Rename the file
        old_path = os.path.join(directory, filename)
        new_path = os.path.join(directory, new_name)
        os.rename(old_path, new_path)
        
        # Create .txt files for beanie and cap items
        if 'beanie' in new_name.lower():
            create_description_file(new_path, "beanie TWELVELABSWEAR with the logo of a company of 4 circles arranged in a grid that also contains the wording \"Twelve Labs\"")
        elif 'cap' in new_name.lower():
            create_description_file(new_path, "cap TWELVELABSWEAR with the logo of a company of 4 circles arranged in a grid that also contains the wording \"Twelve Labs\"")

        print(f"Renamed: {filename} -> {new_name}")

def create_description_file(file_path, description):
    txt_path = os.path.splitext(file_path)[0] + '.txt'
    with open(txt_path, 'w') as f:
        f.write(description)
    print(f"Created description file: {txt_path}")

# Specify the directory path
directory_path = "TWELVELABSHEADGEAR"

# Call the function to rename files
rename_files(directory_path)
