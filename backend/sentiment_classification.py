import os
import json
import argparse
from typing import List, Dict
from transformers import pipeline
from collections import Counter

"""
This file runs sentiment classification on CourseTable data as follows:

Args
- data_path: Path to the desired folder containing .json files for courses
- [OBSOLETE] sentiment_input_fields: List containing desired fields in each course's json object to consider for sentiment analysis

Processing
- Consider each .json file in 'data_path'
- For each item (representing a single course) in the .json: 
    - Retrieve the relevant information specified by 'sentiment_input_fields'
    - Format as string
    - Pass to sentiment analysis model
    - Store result as a new field(s) in the json object

Sentiment Analysis Details
- Model used: https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest?text=Covid+cases+are+increasing+fast%21
- For each review question, apply sentiment analysis to EACH student-written response to the question for a given course
- Count up the # of positive, negative, and neutral labels
- Compute proportions of each label and use the max proportion one as the true lbel
- Update the current course's json object with the following:
    - For each review question:
        - List[str]: sentiment labels for each review
        - List[float]: sentiment scores for each review
        - Dict[float]: proportions of pos/neg/neutral reviews
    - Overall:
        - str: final sentiment label for the course's reviews (averaged across all reviews)
        - float: final sentiment label's proportion score (again across all reviews)

Result
- Updated .json files with new sentiment field for each course's json object
"""

# Load sentiment model for use throughout rest of code
sentiment_analysis = pipeline("sentiment-analysis",model="cardiffnlp/twitter-roberta-base-sentiment-latest", max_length=512, truncation=True)

# Get appropriate most common sentiment label
def get_most_common(
        stats_dict: Counter,
    ):
    if stats_dict['positive'] == stats_dict['neutral'] == 0.5:
        return 'positive', 0.5
    if stats_dict['negative'] == stats_dict['neutral'] == 0.5:
        return 'negative', 0.5
    if stats_dict['negative'] == stats_dict['positive'] == 0.5:
        return 'neutral', 0.0
    return stats_dict.most_common(1)[0]

# Function to perform sentiment analysis
def analyze(
        sentiment_input: str,
    ):
    result = sentiment_analysis(sentiment_input)
    return result[0]['label'], result[0]['score']

# Obtain sentiment results for students' responses to a given evaluation question for a particular course
def process(
        question: str,
    ):
    # If no comments are listed
    if question['comments']==[]:
        return [], [], Counter(), Counter(), ''

    # Initialize counters
    labels = []
    scores = []

    # perform sentiment classification per response
    for comment in question['comments']:
        sentiment_label, sentiment_score = analyze(question['question_text']+"\n"+comment)
        labels.append(sentiment_label)
        scores.append(sentiment_score)
    
    # compute counts per sentiment class & normalize to get distribution
    counts = Counter(labels)
    distr = Counter(labels)
    num_labels = len(labels)
    for sentiment in distr.keys():
        distr[sentiment] /= num_labels
    
    overall_label = get_most_common(counts) # label with max count

    return labels, scores, counts, distr, overall_label

# Main function to loop over all JSON files in a folder
def main(args):

    # Identify relevant data files -- confirm only .jsons are considered & sort alphanumerically for consistency
    all_jsons = sorted(sorted([filename for filename in os.listdir(args.data_path) if filename.endswith(".json")], key=str.lower), key=len)
    
    # Look at all the files
    for idx, filename in enumerate(all_jsons):

        # Start on specified file index
        if idx >= args.start_file_idx:

            # Write current filename to log (in case need to pause/resume later)
            f = open(os.path.join(args.data_path,"0_num_files_analyzed_so_far.txt"), "w")
            f.write("\nOn file: "+filename)
            f.write("\nCorresponding index: "+str(idx))
            f.close()

            # Read the json file for the current course
            file_path = os.path.join(args.data_path, filename)
            with open(file_path, 'r') as file:
                course = json.load(file)

            final_counts = Counter()
            course['sentiment_info'] = {}

            # Check that written reviews are provided for the course
            if course['enrollment']['responses'] > 0:

                # Retrieve relevant review info
                narratives = course['narratives']
                for question in narratives:

                    # What knowledge, skills, and insights did you develop by taking this course?
                    if 'YC401' in question['question_id']:
                        labels, scores, counts, distr, overall_label = process(question)
                        course['sentiment_info']['YC401'] = {
                            'sentiment_labels': labels, 
                            'sentiment_scores': scores,
                            'sentiment_counts': counts, 
                            'sentiment_distribution': distr, 
                            'sentiment_overall': overall_label,
                        }
                        final_counts += counts

                    # What are the strengths and weaknesses of this course and how could it be improved?
                    elif 'YC403' in question['question_id']:
                        labels, scores, counts, distr, overall_label = process(question)
                        course['sentiment_info']['YC403'] = {
                            'sentiment_labels': labels, 
                            'sentiment_scores': scores,
                            'sentiment_counts': counts, 
                            'sentiment_distribution': distr, 
                            'sentiment_overall': overall_label,
                        }
                        final_counts += counts

                    # Would you recommend this course to another student? Please explain.
                    elif 'YC409' in question['question_id']:
                        labels, scores, counts, distr, overall_label = process(question)
                        course['sentiment_info']['YC409'] = {
                            'sentiment_labels': labels, 
                            'sentiment_scores': scores,
                            'sentiment_counts': counts, 
                            'sentiment_distribution': distr, 
                            'sentiment_overall': overall_label,
                        }
                        final_counts += counts

                # Edge case
                if final_counts==Counter():
                    course['sentiment_info']["final_label"] = ''
                    course['sentiment_info']["final_count"] = 0
                    course['sentiment_info']["final_proportion"] = 0.
                    course['sentiment_info']["final_counts"] = Counter()
                    course['sentiment_info']["final_distribution"] = Counter()
                
                # Otherwise, record final results
                else:
                    final_label, final_count = get_most_common(final_counts)
                    final_distr = final_counts.copy()
                    num_labels = sum(final_counts.values())
                    for label in final_distr.keys():
                        final_distr[label] /= num_labels
                    final_label, final_proportion = get_most_common(final_distr)

                    course['sentiment_info']["final_label"] = final_label
                    course['sentiment_info']["final_count"] = final_count
                    course['sentiment_info']["final_proportion"] = final_proportion
                    course['sentiment_info']["final_counts"] = final_counts
                    course['sentiment_info']["final_distribution"] = final_distr

                # Write back the updated data to the same file
                with open(file_path, 'w') as file:
                    json.dump(course, file, indent=4)

            else:
                course['sentiment_info'] = {}
                course['sentiment_info']['YC401'] = {
                            'sentiment_labels': [], 
                            'sentiment_scores': [],
                            'sentiment_counts': Counter(), 
                            'sentiment_distribution': Counter(), 
                            'sentiment_overall': '',
                        }
                course['sentiment_info']['YC403'] = {
                            'sentiment_labels': [], 
                            'sentiment_scores': [],
                            'sentiment_counts': Counter(), 
                            'sentiment_distribution': Counter(), 
                            'sentiment_overall': '',
                        }
                course['sentiment_info']['YC409'] = {
                            'sentiment_labels': [], 
                            'sentiment_scores': [],
                            'sentiment_counts': Counter(), 
                            'sentiment_distribution': Counter(), 
                            'sentiment_overall': '',
                        }
                course['sentiment_info']["final_label"] = ''
                course['sentiment_info']["final_count"] = 0
                course['sentiment_info']["final_proportion"] = 0.
                course['sentiment_info']["final_counts"] = Counter()
                course['sentiment_info']["final_distribution"] = Counter()

                # Write back the updated data to the same file
                with open(file_path, 'w') as file:
                    json.dump(course, file, indent=4)

            print("Finished",filename)


############################################################
############ RUN SENTIMENT CLASSIFICATION HERE #############
############################################################

# Call the main function to process all JSON files
# Example call: python sentiment_classification.py --sentiment_input_fields title code --data_path data/test_courses
# Example call #2: python backend/sentiment_classification.py --data_path=./data/course_evals
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # Specify the folder path where JSON files are located
    parser.add_argument("--data_path", 
                        type=str, 
                        default="data/test_courses",
                        help="Folder where the .json files for the course data are located") 

    parser.add_argument("--start_file_idx", 
                        type=int, 
                        default=0,
                        help="Specify which index of file to start sentiment analysis on. For when the run is paused and desired to be resumed later.") 

    # parser.add_argument("--sentiment_input_fields", 
    #                     nargs="*",  # 0 or more values expected => creates a list
    #                     type=str,
    #                     default = ['narratives'] # other options: title, code
    #                     help="Specify what field(s)/attribute(s) of each course to use to run sentiment classification") 

    args = parser.parse_args()

    main(args)

