# Transforming the Repo into a command line tool

## Functions this repo is supposed to perform

- Take a subject path consisting pdf of chapters, take a output csv path, and output concepts csv
- Take a subject path consisting pdf of chapters, take a output json path, and output exercise question json
- Take a subject path consisting pdf of chapters, take a output json path, and output solved examples json
- Take a subject path consisting of concept csvs of chapters, and upload it to supabase
- Take a subject path consisting of exercise question jsons of chapters, and upload it to supabase
- Take a subject path consisting of solved examples jsons of chapters, and upload it to supabase

## In detailed functions

### Subject -> Concept CSV

- Command
    - `python concepts_builder.py --input_dir <subject_directory_path> --output_dir <concept_csv_output_directory_path> --subject_id <subject_id_for_uuid_generation>`
- Inputs:
    - Subject directory path consisting pdf of chapters
    - Output directroy path for saving the concept csvs
    - Subject ID for generating UUIDs
- Performs:
    - For each chapter pdf, extract the text and generate a concept csv using the existing code in this repo
    - Save the generated concept csv in the output directory with the same name as the chapter pdf but with .csv extension

### Subject -> Exercise Question JSON

- Command
    - `python exercise_questions_builder.py --input_dir <subject_directory_path> --output_dir <exercise_question_json_output_directory_path> --subject_id <subject_id_for_uuid_generation>`
- Inputs:
    - Subject directory path consisting pdf of chapters
    - Output directroy path for saving the exercise question jsons
    - Subject ID for generating UUIDs
- Performs:
    - For each chapter pdf, extract the text and generate an exercise question json using the existing code in this repo
    - Save the generated exercise question json in the output directory with the same name as the chapter pdf but with .json extension

### Subject -> Solved Examples JSON

- Command
    - `python solved_examples_builder.py --input_dir <subject_directory_path> --output_dir <solved_examples_json_output_directory_path> --subject_id <subject_id_for_uuid_generation>`
- Inputs:
    - Subject directory path consisting pdf of chapters
    - Output directroy path for saving the solved examples jsons
    - Subject ID for generating UUIDs
- Performs:
    - For each chapter pdf, extract the text and generate a solved examples json using the existing code in this repo
    - Save the generated solved examples json in the output directory with the same name as the chapter pdf but with .json extension

### Concept CSV -> Supabase
- Command
    - `python concepts_uploader.py --input_dir <concept_csv_directory_path>`
- Inputs:
    - Subject directory path consisting concept csvs of chapters
- Performs:
    - For each chapter concept csv, read the csv and upload the concepts to supabase using the existing code in this repo
    - (ids will be present in csv itself, so no need to generate ids here)

### Exercise Question JSON -> Supabase
- Command
    - `python exercise_questions_uploader.py --input_dir <exercise_question_json_directory_path>`
- Inputs:
    - Subject directory path consisting exercise question jsons of chapters
- Performs:
    - For each chapter exercise question json, read the json and upload the exercise questions to supabase using the existing code in this repo
    - (ids will be present in json itself, so no need to generate ids here)

### Solved Examples JSON -> Supabase
- Command
    - `python solved_examples_uploader.py --input_dir <solved_examples_json_directory_path>`
- Inputs:
    - Subject directory path consisting solved examples jsons of chapters
- Performs:
    - For each chapter solved examples json, read the json and upload the solved examples to supabase using the existing code in this repo
    - (ids will be present in json itself, so no need to generate ids here)


## UUID System for Unique Identification
To ensure that each concept, exercise question, and solved example is uniquely identifiable across the entire subject, we will implement a UUID (Universally Unique Identifier) system. This will allow us to maintain consistency and avoid any conflicts when uploading data to Supabase.
UUID5 will be used to generate unique identifiers based on the content of the concept, exercise question, or solved example. This means that if the same content is processed multiple times, it will generate the same UUID, ensuring idempotency in our uploads.

### Board Creation

- Board is to be created manually, and the board ID is to be copied and used in the code for uploading data to the correct board in Supabase.

### School Class Creation

- School Class ID = UUID5(board_id, school_class_name), to be created manually for each class.

### Subject Creation

- Subject ID = UUID5(school_class_id, subject_name), to be created manually for each subject.

### Chapter Creation

- Chapter ID = UUID5(subject_id, chapter_name) (To be added in the code for generating concept csv)

### Topic Creation

- Topic ID = UUID5(chapter_id, topic_name) (To be added in the code for generating concept csv, exercise question json, and solved examples json)

### Concept Creation

- Concept ID = UUID5(topic_id, concept_name) (To be added in the code for generating concept csv)

### Exercise Question Creation

- Exercise Question ID = UUID5(subject_id, exercise_question_json_text) (To be added in the code for generating exercise question json)

### Solved Example Creation

- Solved Example ID = UUID5(subject_id, solved_example_json_text) (To be added in the code for generating solved examples json)

## Instructions

- Supabase insertion process will have the uuids generated in the code for generating concept csv, exercise question json, and solved examples json, and these uuids will be used while uploading to supabase to maintain consistency and avoid conflicts.