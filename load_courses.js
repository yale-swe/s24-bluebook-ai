/* global use, db */
// MongoDB Playground
// To disable this template go to Settings | MongoDB | Use Default Template For Playground.
// Make sure you are connected to enable completions and to be able to run a playground.
// Use Ctrl+Space inside a snippet or a string literal to trigger completions.
// The result of the last command run in a playground is shown on the results panel.
// By default the first 20 documents will be returned with a cursor.
// Use 'console.log()' to print to the debug output.
// For more documentation on playgrounds please refer to
// https://www.mongodb.com/docs/mongodb-vscode/playgrounds/

// Select the database to use.
use('course_db');
const fs = require('fs');
const path = require('path');


// Directory containing your JSON files
const directoryPath = '/Users/buweichen/repos/s24-bluebook-ai/data/parsed_courses/'; // Replace with your directory path
function loadSeasonCourses() {
    const collection = db.getCollection('parsed_courses')

    const files = fs.readdirSync(directoryPath);
    
    console.log(files)

    for (const file of files) {
      if (file.endsWith('.json') && /^(2021|2022|2023|2024)(01|02|03)\.json$/.test(file)) {
        const filePath = path.join(directoryPath, file);
        const fileContents = fs.readFileSync(filePath);
        console.log(fileContents);
        const courses = JSON.parse(fileContents);
        if (Array.isArray(courses)) {
          collection.insertMany(courses);
          console.log(`Inserted courses from ${file}`);
        }
      }
    }
}
loadSeasonCourses();