# not functional at the moment, reason unknown

import pymongo
import json
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection setup

client = pymongo.MongoClient(os.getenv("MONGODB_URI"))  # Replace with your MongoDB URI
db = client[os.getenv("DB_NAME")]                 # Replace with your database name
season_courses_collection = db['season_courses']  # Collection for season courses

# Function to load and insert data
def load_data(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.json') and filename[:4] in ["2021", "2022", "2023", "2024"] and filename[4:6] in ["01", "02", "03"] and len(filename) == 11:
            with open(os.path.join(directory, filename), 'r') as file:
                data = json.load(file)
                if isinstance(data, list):  # Check if the data is a list
                    season_courses_collection.insert_many(data)  # Insert all courses from the file

# Replace with the path to your 'season_courses' directory
load_data('/Users/buweichen/repos/s24-bluebook-ai/data/season_courses')

# Close the MongoDB connection
client.close()
