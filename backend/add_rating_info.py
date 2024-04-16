import os
import json
import argparse
import subprocess
import os
import json
import shutil

"""
This file directly adds coursetable rating data to .json files in a directory of choice:

Args
- target_data_path: Path to the desired folder containing .json files for courses that must be updated with rating info
- rating_data_path: Path to folder containing .json files equipped with rating info
- years_to_port: List containing integers representing what years of rating info to include in the given .json files for parsed courses

Processing
- Consider each .json file in 'data_path'
- For each item (representing a single course) in the .json: 
    - Retrieve the relevant course evaluation files for the year(s) specified
    - Store result as a new field(s) in the json course_objectect

Result
- Updated .json files with new rating field for each course's json course_objectect, written in-place.
"""

# Main function to loop over all JSON course_objectects for the given year
def main(args):

    # Look at all parsed course files
    for filename in os.listdir(args.target_data_path):
        # import ipdb; ipdb.set_trace()

        # Consider each file for the relevant years & load
        if filename.endswith(".json") and int(filename[:4]) in args.years_to_port:
            print("On year", filename)

            season_file_path = os.path.join(args.target_data_path, filename)
            with open(season_file_path, 'r') as f:
                season_course = json.load(f)
            
            # Consider each course in the relevant year/season
            count = 0
            for course_object in season_course:
                reviews_missing = True

                season_code = course_object.get("season_code", "")
                crns = course_object.get("crns")
                count += 1

                # Identify the CRN of the course
                for crn in crns:
                    print(f"On: {season_code}-{crn} / index {count}")

                    # Inspect if there are any json entries for that course in the specified season
                    grep_cmd = f"ls {args.rating_data_path} | grep {season_code}-{crn}"
                    try: # if so, write the rating data to the file
                        grep_output = subprocess.check_output(grep_cmd, shell=True).decode().strip().split("\n")
                        season_filename = grep_output[0]
                        rating_file_path = os.path.join(args.rating_data_path, season_filename)
                        with open(rating_file_path, 'r') as rating_file:
                            rating_json = json.load(rating_file)
                            course_object["ratings"] = rating_json["ratings"]
                        print(f"Finished {season_code}-{crn}")
                        reviews_missing = False
                        break
                    except: # if no matches found, continue
                        continue
                if reviews_missing:
                    course_object["ratings"] = []

            with open(season_file_path, 'w') as f:
                json.dump(season_course, f, indent=4)


############################################################
############ RUN HERE #############
############################################################

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # Specify the folder path where JSON files are located
    parser.add_argument("--target_data_path", 
                        type=str, 
                        default="data/parsed_courses",
                        help="Folder where the .json files that need rating info copied over are located.") 

    parser.add_argument("--rating_data_path", 
                        type=str, 
                        default="data/course_evals",
                        help="Folder where the .json files with rating info are located.") 

    parser.add_argument("--years_to_port", 
                        nargs="*",  # 0 or more values expected => creates a list
                        type=int,
                        default = [2023], # other options: YC401, YC403
                        help="Specify what years of rating info to include in the parsed course data .json files.") 

    args = parser.parse_args()

    main(args)

