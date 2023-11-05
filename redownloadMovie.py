import os
import csv
import requests

# Define Radarr API settings
RADARR_API_KEY = 'a74d42e9c38944c7bb6098f1f79caa5d'
RADARR_URL = 'http://192.168.1.114:7878'  # Adjust to your Radarr URL
RADARR_PROFILE_ID = 7  # Replace with the desired profile ID

# CSV file containing movie inspection results
CSV_FILENAME = 'movie_inspection_results.csv'

# Function to delete movie files and trigger redownload in Radarr
def redownload_movie(movie_folder):
    # Step 1: Delete the movie files
    for root, dirs, files in os.walk(movie_folder):
        for file in files:
            file_path = os.path.join(root, file)
            os.remove(file_path)
    
    # Step 2: Trigger redownload in Radarr
    movie_title = os.path.basename(movie_folder)
    payload = {
        'title': movie_title,
        'profileId': RADARR_PROFILE_ID
    }
    headers = {
        'X-Api-Key': RADARR_API_KEY
    }
    response = requests.post(f'{RADARR_URL}/api/v3/movie', json=payload, headers=headers)
    if response.status_code == 201:
        print(f"Redownloading '{movie_title}' in Radarr.")
    else:
        print(f"Failed to redownload '{movie_title}' in Radarr.")

# Read the CSV file and process each movie
with open(CSV_FILENAME, newline='') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        movie_folder = os.path.join('/media/Movies', row['Folder Name'])
        additional_files = row['Additional Movie Files'].split(', ')
        # Check if the movie needs to be redownloaded
        file_size = int(row['File Size'])
        if (file_size > 5 * 1024 * 1024 * 1024) or (row['Movie Codec'] != 'HEVC'):
            redownload_movie(movie_folder)
