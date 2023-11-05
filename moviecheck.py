import os
import csv
import subprocess

# List of file extensions to be ignored
IGNORED_EXTENSIONS = {'.dat','.jpg', '.jpeg', '.png', '.srt', '.sub', '.idx', '.nfo', '.txt', '.db', '.ico', '.sample', '.tbn', '.xml', '.srr','.log''.md5'}
IGNORED_FILES = {'.DS_Store','._.DS_Store'}

# Define the CSV file and headings
CSV_FILENAME = 'movie_inspection_results.csv'
CSV_HEADINGS = [
    'Movie Title',
    'Movie Codec',
    'File Size',
    'Folder Name',
    'Multiple Movie Files? (Y/N)',
    'Additional Movie Files'
]

# Create or open the CSV file for writing
with open(CSV_FILENAME, 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(CSV_HEADINGS)  # Write the headings to the CSV file

    # Function to simulate inspecting a movie file for its properties (e.g., codec)
    def inspect_movie(movie_path):
        #use mediainfo to read the media file metadata
        mediainfo_output = subprocess.check_output(['mediainfo', '--Inform=Video;%Format%', movie_path], universal_newlines=True).strip()
        # Replace this section with code to inspect the movie file
        movie_properties = {
            'Title': os.path.basename(movie_path),
            'Codec': mediainfo_output,
            'Size': os.path.getsize(movie_path),
            'Folder': os.path.basename(os.path.dirname(movie_path))
        }
        return movie_properties

    # Function to simulate checking criteria and making decisions
    def check_and_write(movie_path):
        # Ignore files with specific extensions
        file_extension = os.path.splitext(movie_path)[-1].lower()
        if file_extension in IGNORED_EXTENSIONS or os.path.basename(movie_path) in IGNORED_FILES:
            return

        movie_properties = inspect_movie(movie_path)
        
        # Criteria 1: Large File Size
        size_criteria_met = movie_properties['Size'] > 5 * 1024 * 1024 * 1024  # 5GB

        # Criteria 2: Codec
        codec_criteria_met = movie_properties['Codec'] == 'HEVC'  # Desired codec

        # Criteria 3: File Extension
        extension_criteria_met = movie_path.lower().endswith('.mkv')

        # Criteria 4: Multiple Video Files in One Folder
        folder_path = os.path.dirname(movie_path)
        video_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.avi', '.mp4', '.mkv', '.mov'))]
        multiple_files_criteria_met = len(video_files) > 1
        
        additional_files = ', '.join([f for f in video_files if f != os.path.basename(movie_path)])
        
        # Write the results to the CSV file
        csv_writer.writerow([
            movie_properties['Title'],
            movie_properties['Codec'],
            movie_properties['Size'],
            movie_properties['Folder'],
            'Y' if multiple_files_criteria_met else 'N',
            additional_files
        ])

        # Decision: Should the movie be re-downloaded?
        if size_criteria_met or not codec_criteria_met or not extension_criteria_met or multiple_files_criteria_met:
            print(f"Movie '{movie_properties['Title']}' does not meet one or more criteria and should be re-downloaded.")

    # Replace this with the actual path to your movie files directory
    movie_files_directory = '/media/Movies'

    # Loop through the movie files and check each one
    for root, dirs, files in os.walk(movie_files_directory):
        for file in files:
            movie_path = os.path.join(root, file)
            check_and_write(movie_path)
