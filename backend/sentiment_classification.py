import os
import json
import argparse
from typing import List, Dict
from transformers import pipeline

"""
This file runs sentiment classification on CourseTable data as follows:

Args
- data_path: Path to the desired folder containing .json files for courses
- sentiment_input_fields: List containing desired fields in each course's json object to consider for sentiment analysis

Processing
- Consider each .json file in 'data_path'
- For each item in the .json: 
    - Retrieve the relevant information specified by 'sentiment_input_fields'
    - Format as string
    - Pass to sentiment analysis model
    - Store result as a new field(s) in the json object

Sentiment Analysis Details
- Model used: https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest?text=Covid+cases+are+increasing+fast%21
- TODO: 
    - Refactor so that EACH review has the sentiment analysis applied to it, then count up # of positive, negative, and neutral results, 
      compute proportions of each and use the max proportion one as the label
    - Store the following in updated json objects:
        - List[str]: sentiment labels for each review
        - List[float]: sentiment scores for each review
        - List[float]: proportions of pos/neg/neutral reviews (or Dict?)
        - str: final sentiment label
        - float: final sentiment label's proportion score

Result
- Updated .json files with new sentiment field(s) for each course's json object
"""

# Function to perform sentiment analysis
def analyze(
        sentiment_input: str,
    ):
    # sentiment_analysis = pipeline("sentiment-analysis",model="siebert/sentiment-roberta-large-english")
    sentiment_analysis = pipeline("sentiment-analysis",model="cardiffnlp/twitter-roberta-base-sentiment-latest")
    result = sentiment_analysis(sentiment_input)
    import ipdb; ipdb.set_trace
    return result[0]['label'], result[0]['score']

# Convert sentiment input to a string
def stringify(
        sentiment_inputs: List[str],
    ):
    sentiment_string = ""
    for field, value in sentiment_inputs.items():
        sentiment_string += f"{field}: {value}\n"
    return sentiment_string.strip()

# Main function to loop over all JSON files in a folder
def main(args):

    # Look at all data files
    for filename in os.listdir(args.data_path):

        # Confirm only .jsons are considered 
        if filename.endswith(".json"):

            # Read the json file
            file_path = os.path.join(args.data_path, filename)
            with open(file_path, 'r') as file:
                data = json.load(file)

            # Add sentiment field to each json object
            for course in data:

                # Retrieve relevant sentiment info for current course
                sentiment_inputs = {}
                for field in args.sentiment_input_fields:
                    sentiment_inputs[field] = course.get(field)
                
                # Perform sentiment classification
                stringified_inputs = stringify(sentiment_inputs)
                sentiment_label, sentiment_score = analyze(stringified_inputs)

                # Update the course with sentiment classification result
                # course["sentiment_labels"] = 
                # course["sentiment_scores"] = 
                # course["sentiment_distribution"] = 
                course["final_sentiment"] = sentiment_label
                course["final_sentiment_proportion"] = sentiment_score
                # course.pop("stringified_info")

            # Write back the updated data to the same file
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)


############################################################
############ RUN SENTIMENT CLASSIFICATION HERE #############
############################################################

# Call the main function to process all JSON files
# Example call: python sentiment_classification.py --sentiment_input_fields title code --data_path data/test_courses
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # Specify the folder path where JSON files are located
    parser.add_argument("--data_path", 
                        type=str, 
                        default="data/test_courses",
                        help="Folder where the .json files for the course data are located") 

    parser.add_argument("--sentiment_input_fields", 
                        nargs="*",  # 0 or more values expected => creates a list
                        type=str,
                        default=["title", "code"],
                        help="Specify what field(s)/attribute(s) of each course to use to run sentiment classification") 

    args = parser.parse_args()

    main(args)

