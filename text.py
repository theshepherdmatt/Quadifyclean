import os

# Define the path to the folder containing your Python scripts and the output file path
folder_path = '/home/volumio/Quadifyclean/tests/'
output_file = 'combined_scripts.txt'

# Open the output file in write mode
with open(output_file, 'w') as outfile:
    # Loop through all files in the specified folder
    for filename in os.listdir(folder_path):
        # Process only .py files
        if filename.endswith('.py'):
            file_path = os.path.join(folder_path, filename)
            # Write the file name to the output file for separation
            outfile.write(f'# File: {filename}\n')
            # Open each Python file and read its contents
            with open(file_path, 'r') as infile:
                # Write the contents of the Python file to the output file
                outfile.write(infile.read())
                outfile.write('\n\n')  # Add a blank line between scripts

