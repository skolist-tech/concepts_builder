# Concepts Builder

A CLI tool for extracting structured educational content from textbook PDFs using AI. Generates concepts, solved examples, and exercise questions with deterministic UUIDs, then uploads them to a Supabase database.

## Overview

This tool provides CLI commands for the content extraction pipeline:

### ID Generation Commands
- **`generate_school_class_id.py`** - Generate school_class UUID from board_id + school_class_name
- **`generate_subject_id.py`** - Generate subject UUID from school_class_id + subject_name

### Database Record Commands (Manage records in Supabase)
- **`boards.py`** - Add or get board records in Supabase
- **`school_class.py`** - Add or get school_class records in Supabase with deterministic UUID
- **`subject.py`** - Add or get subject records in Supabase with deterministic UUID

### Generation Commands (PDF → CSV/JSON with UUIDs)
1. **`concepts_builder.py`** - Extract concepts from PDFs → CSV with chapter/topic/concept UUIDs
2. **`exercise_questions_builder.py`** - Extract exercise questions → JSON with question UUIDs
3. **`solved_examples_builder.py`** - Extract solved examples → JSON with question UUIDs

### Upload Commands (CSV/JSON → Supabase)
4. **`concepts_uploader.py`** - Upload concept CSVs to Supabase
5. **`exercise_questions_uploader.py`** - Upload exercise question JSONs to Supabase
6. **`solved_examples_uploader.py`** - Upload solved examples JSONs to Supabase

### Migration Commands
- **`migrate_add_uuids.py`** - Add UUIDs to existing CSV/JSON files without them

### Verification Commands
- **`verify_concept_exercise_solved_example.py`** - Verify consistency between CSVs and JSONs

## Prerequisites

- **Python 3.11+**
- **uv** - Python package manager ([install guide](https://github.com/astral-sh/uv))
- **Gemini API Key** - For AI-powered content extraction
- **Supabase** - Running instance for upload

## Installation

```bash
# Clone and navigate to the repo
cd concepts_builder

# Install dependencies
uv sync
```

## Configuration

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Required environment variables:

| Variable               | Description                                                 |
| ---------------------- | ----------------------------------------------------------- |
| `GEMINI_API_KEY`       | Google Gemini API key                                       |
| `SUPABASE_URL`         | Your Supabase project URL (local: `http://localhost:54321`) |
| `SUPABASE_SERVICE_KEY` | Supabase service role key                                   |

## UUID System

All IDs are generated using deterministic **UUID5** based on content:

```
board_id (provided)
    └── school_class_id = UUID5(board_id, school_class_name)
            └── subject_id = UUID5(school_class_id, subject_name)
                    └── chapter_id = UUID5(subject_id, chapter_name)
                            └── topic_id = UUID5(chapter_id, topic_name)
                                    └── concept_id = UUID5(topic_id, concept_name)

subject_id
    └── question_id = UUID5(subject_id, question_fingerprint)
```

This ensures:
- **Idempotency**: Running the same command twice produces identical UUIDs
- **No duplicates**: Re-uploading won't create duplicate records
- **Reproducibility**: Same input always produces same output

## CLI Usage

### Generate IDs

Before running the pipeline, generate the required UUIDs:

```bash
# Generate school_class_id from board_id + school_class_name
python generate_school_class_id.py \
    --board_id 550e8400-e29b-41d4-a716-446655440000 \
    --school_class_name "Class 6"
# Output: 7cd86129-fb77-5fae-829a-3a4ec87c1669

# Generate subject_id from school_class_id + subject_name
python generate_subject_id.py \
    --school_class_id 7cd86129-fb77-5fae-829a-3a4ec87c1669 \
    --subject_name "Mathematics"
# Output: 2176654b-2688-5e0c-8910-2e2f8ee596d1
```

Use the generated `subject_id` in the builder commands below.

### Manage Boards

Add or get board records in Supabase:

```bash
# Add a new board
python boards.py --add-board --name "CBSE" --description "Central Board of Secondary Education"

# Get a specific board by ID
python boards.py --get-board --board-id 550e8400-e29b-41d4-a716-446655440000

# Search boards by name (case-insensitive, partial match)
python boards.py --get-board --name "CBSE"

# List all boards
python boards.py --get-board --all
```

**Output (add):**
```
==================================================
Board Created Successfully
==================================================
Board ID:      550e8400-e29b-41d4-a716-446655440000
Board Name:    CBSE
Description:   Central Board of Secondary Education
==================================================
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--add-board` | Either | Add a new board (mutually exclusive with --get-board) |
| `--get-board` | Either | Get board(s) from database (mutually exclusive with --add-board) |
| `--name` | For add/get | Board name (required for add, optional for get to search by name) |
| `--description` | No | Board description |
| `--board-id` | For get | Board UUID to fetch |
| `--all` | For get | List all boards |

### Manage School Classes

Add or get school_class records in Supabase:

```bash
# Add a new school class (by board ID)
python school_class.py --add --board-id 550e8400-e29b-41d4-a716-446655440000 --name "Class 6" --position 6

# Add a new school class (by board name)
python school_class.py --add --board-name "CBSE" --name "Class 6" --position 6

# Get a specific school class by ID
python school_class.py --get --school-class-id 7cd86129-fb77-5fae-829a-3a4ec87c1669

# Search school classes by name (case-insensitive, partial match)
python school_class.py --get --name "Class 6"

# List all school classes for a board
python school_class.py --get --board-id 550e8400-e29b-41d4-a716-446655440000

# List all school classes
python school_class.py --get --all
```

**Output (add):**
```
==================================================
School Class Created Successfully
==================================================
Board ID:    550e8400-e29b-41d4-a716-446655440000
Board Name:  RBSE
School Class Name:  Class 6
School Class ID:    7cd86129-fb77-5fae-829a-3a4ec87c1669
Position:    6
==================================================
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--add` | Either | Add a new school class (mutually exclusive with --get) |
| `--get` | Either | Get school class(es) from database (mutually exclusive with --add) |
| `--board-id` | For add/get | Board UUID (for add or to list all classes) |
| `--board-name` | For add | Board name to look up (alternative to --board-id; errors if duplicates exist) |
| `--name` | For add/get | Class name (required for add, optional for get to search by name) |
| `--position` | For add | Position/order of the class (e.g., 6 for Class 6) |
| `--school-class-id` | For get | School class UUID to fetch |
| `--all` | For get | List all school classes |

### Manage Subjects

Add or get subject records in Supabase:

```bash
# Add a new subject (by school class ID)
python subject.py --add --school-class-id 7cd86129-fb77-5fae-829a-3a4ec87c1669 --name "Mathematics"

# Add a new subject (by board name + school class name)
python subject.py --add --board-name "CBSE" --school-class-name "Class 6" --name "Mathematics"

# Get a specific subject by ID
python subject.py --get --subject-id 2176654b-2688-5e0c-8910-2e2f8ee596d1

# Search subjects by name (case-insensitive, partial match)
python subject.py --get --name "Math"

# List all subjects for a school class
python subject.py --get --school-class-id 7cd86129-fb77-5fae-829a-3a4ec87c1669

# List all subjects
python subject.py --get --all
```

**Output (add):**
```
==================================================
Subject Created Successfully
==================================================
Board ID:      550e8400-e29b-41d4-a716-446655440000
Board Name:    RBSE
Class ID:      7cd86129-fb77-5fae-829a-3a4ec87c1669
Class Name:    Class 6
Subject Name:  Mathematics
Subject ID:    2176654b-2688-5e0c-8910-2e2f8ee596d1
==================================================
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--add` | Either | Add a new subject (mutually exclusive with --get) |
| `--get` | Either | Get subject(s) from database (mutually exclusive with --add) |
| `--school-class-id` | For add/get | School class UUID (for add or to list all subjects) |
| `--board-name` | For add | Board name (use with --school-class-name as alternative to --school-class-id) |
| `--school-class-name` | For add | School class name (use with --board-name as alternative to --school-class-id) |
| `--name` | For add/get | Subject name (required for add, optional for get to search by name) |
| `--subject-id` | For get | Subject UUID to fetch |
| `--all` | For get | List all subjects |

### Step 1: Generate Concepts

Extract chapter → topic → concept hierarchy from PDFs:

```bash
python concepts_builder.py \
    --input_dir ./data/rbse/maths_6_corodova \
    --output_dir ./output/maths_6 \
    --subject_id 11ea3956-d46e-4476-bb2c-a50afa027f5c \
    --prompt_file_path ./prompts/maths_6_concepts.txt
```

By default, chapters whose output CSV already exists in the output directory are **skipped**. To force reprocessing of all chapters (overwriting existing CSVs), use `--reprocess`:

```bash
python concepts_builder.py \
    --input_dir ./data/rbse/maths_6_corodova \
    --output_dir ./output/maths_6 \
    --subject_id 11ea3956-d46e-4476-bb2c-a50afa027f5c \
    --prompt_file_path ./prompts/maths_6_concepts.txt \
    --reprocess
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--input_dir` | Yes | Subject directory containing chapter PDFs |
| `--output_dir` | Yes | Output directory for concept CSVs |
| `--subject_id` | Yes | Subject UUID for generating deterministic UUIDs |
| `--prompt_file_path` | Yes | Path to the prompt file for concept extraction |
| `--reprocess` | No | Reprocess all chapters even if output CSV already exists (default: skip existing) |

**Output:** `{chapter_name}_concepts.csv` with columns:
- `concept_id`, `concept_name`, `concept_description`, `concept_page_number`
- `topic_id`, `topic_name`, `topic_description`, `topic_position`
- `chapter_id`, `chapter_name`, `chapter_description`, `chapter_position`
- `subject_id`

### Step 2: Generate Solved Examples

Extract worked examples mapped to concepts (requires concept CSVs):

```bash
python solved_examples_builder.py \
    --input_dir ./data/rbse/maths_6_corodova \
    --output_dir ./output/maths_6 \
    --subject_id 11ea3956-d46e-4476-bb2c-a50afa027f5c \
    --prompt_file_path ./prompts/maths_6_solved.txt
```

By default, chapters whose output JSON already exists are **skipped**. To force reprocessing, use `--reprocess`:

```bash
python solved_examples_builder.py \
    --input_dir ./data/rbse/maths_6_corodova \
    --output_dir ./output/maths_6 \
    --subject_id 11ea3956-d46e-4476-bb2c-a50afa027f5c \
    --prompt_file_path ./prompts/maths_6_solved.txt \
    --reprocess
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--input_dir` | Yes | Subject directory containing chapter PDFs |
| `--output_dir` | Yes | Output directory for solved examples JSONs (should also contain concept CSVs) |
| `--subject_id` | Yes | Subject UUID for generating deterministic UUIDs |
| `--prompt_file_path` | Yes | Path to the prompt file for solved examples extraction |
| `--reprocess` | No | Reprocess all chapters even if output JSON already exists (default: skip existing) |

**Output:** `{chapter_name}_solved_examples.json` with:
- `chapter_name`, `chapter_id`, `subject_id`
- `solved_examples_questions[]` - each with `id`, `question_text`, `explanation`, etc.

### Step 3: Generate Exercise Questions

Extract practice problems mapped to concepts (requires concept CSVs):

```bash
python exercise_questions_builder.py \
    --input_dir ./data/rbse/maths_6_corodova \
    --output_dir ./output/maths_6 \
    --subject_id 11ea3956-d46e-4476-bb2c-a50afa027f5c \
    --prompt_file_path ./prompts/maths_6_exercises.txt
```

By default, chapters whose output JSON already exists are **skipped**. To force reprocessing, use `--reprocess`:

```bash
python exercise_questions_builder.py \
    --input_dir ./data/rbse/maths_6_corodova \
    --output_dir ./output/maths_6 \
    --subject_id 11ea3956-d46e-4476-bb2c-a50afa027f5c \
    --prompt_file_path ./prompts/maths_6_exercises.txt \
    --reprocess
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--input_dir` | Yes | Subject directory containing chapter PDFs |
| `--output_dir` | Yes | Output directory for exercise question JSONs (should also contain concept CSVs) |
| `--subject_id` | Yes | Subject UUID for generating deterministic UUIDs |
| `--prompt_file_path` | Yes | Path to the prompt file for exercise question extraction |
| `--reprocess` | No | Reprocess all chapters even if output JSON already exists (default: skip existing) |

**Output:** `{chapter_name}_exercise_questions.json`

### Step 4: Verify Files (REQUIRED before upload)

**Always verify files before uploading to Supabase** to catch mismatches early:

```bash
python verify_concept_exercise_solved_example.py \
    --input_dir ./output/maths_6 \
    --check-chapters --check-concepts --check-conventions
```

Fix any failures before proceeding:
- **Chapter mismatches**: Re-run `migrate_add_uuids.py` to regenerate UUIDs
- **Concept mismatches**: Add missing concepts to CSV or rename concepts in JSON
- **Convention failures**: Rename files to match pattern `{number}_{name}_{type}.{ext}`

### Step 5: Upload Concepts

Upload concept CSVs to Supabase:

```bash
python concepts_uploader.py --input_dir ./output/maths_6
```

### Step 6: Upload Solved Examples

Upload solved examples JSONs to Supabase:

```bash
python solved_examples_uploader.py --input_dir ./output/maths_6
```

### Step 7: Upload Exercise Questions

Upload exercise question JSONs to Supabase:

```bash
python exercise_questions_uploader.py --input_dir ./output/maths_6
```

### Migrate Legacy Files (Add UUIDs)

Add UUIDs to existing CSV/JSON files that don't have them:

```bash
python migrate_add_uuids.py \
    --input_dir ./data/rbse_output/maths_6_corodova \
    --output_dir ./data/output_with_uuids/maths_6_corodova \
    --subject_id 2176654b-2688-5e0c-8910-2e2f8ee596d1
```

Processes all `*_concepts.csv`, `*_exercise_questions.json`, and `*_solved_examples.json` files in the directory, adding deterministic UUIDs.

### Verify Files (Check Consistency)

Verify that concept CSVs and question JSONs are consistent:

```bash
# Check chapter_name and chapter_id match between CSVs and JSONs
python verify_concept_exercise_solved_example.py \
    --input_dir ./output/maths_6 \
    --check-chapters

# Check that concepts referenced in questions exist in concept CSVs
python verify_concept_exercise_solved_example.py \
    --input_dir ./output/maths_6 \
    --check-concepts

# Check concepts with AI-powered suggestions for missing mappings
python verify_concept_exercise_solved_example.py \
    --input_dir ./output/maths_6 \
    --check-concepts --suggest

# Check file naming conventions and position consistency
python verify_concept_exercise_solved_example.py \
    --input_dir ./output/maths_6 \
    --check-conventions

# Run all checks
python verify_concept_exercise_solved_example.py \
    --input_dir ./output/maths_6 \
    --check-chapters --check-concepts --check-conventions
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--input_dir` | Yes | Directory containing concept CSVs and question JSONs |
| `--check-chapters` | Either | Check chapter_name and chapter_id consistency |
| `--check-concepts` | Either | Check that concepts referenced in questions exist in CSVs |
| `--check-conventions` | Either | Check file naming conventions and position consistency |
| `--suggest` | No | Use Gemini AI to suggest correct concept mappings for missing concepts (requires --check-concepts) |

**Output:**
```
======================================================================
CHAPTER CONSISTENCY CHECK
======================================================================
   1. 01_knowing_our_numbers                       [PASS]
   2. 02_whole_numbers                             [PASS]
  11. 11_linear_equations                          [FAIL]
      -> Exercise JSON chapter_id mismatch: CSV='0b1c52b4...' vs JSON='88a56fde...'
======================================================================
Chapter check: 10 passed, 1 failed

======================================================================
CONCEPT MAPPING CHECK
======================================================================
   1. 01_knowing_our_numbers                       [PASS]
  16. 16_data_handling                             [FAIL] - 2 missing concepts
      -> [Exercise] Interpreting Pie Charts
         Suggestions: Interpreting Pie Chart Data, Pie Chart Interpretation
      -> [Solved] Comparing Decimals
         Suggestions: Comparing Unlike Decimals, Decimal Comparison
======================================================================
Concept check: 15 passed, 1 failed

======================================================================
FILE CONVENTIONS CHECK
======================================================================
   1. 01_knowing_our_numbers                       [PASS]
   2. 02_whole_numbers                             [FAIL]
      -> Filename number (02) != chapter_position (3)
      -> Missing exercise JSON: 02_whole_numbers_exercise_questions.json
======================================================================
Conventions check: 1 passed, 1 failed
```

When concepts are missing, the tool uses **subsequence matching** to suggest similar concepts from the CSV. This helps identify typos or slight naming differences.

| Argument | Required | Description |
|----------|----------|-------------|
| `--input_dir` | Yes | Directory containing concept CSVs and question JSONs |
| `--check-chapters` | No | Check chapter_name and chapter_id consistency (also checks internal CSV row consistency) |
| `--check-concepts` | No | Check that concepts in questions exist in CSVs (with suggestions for mismatches) |
| `--check-conventions` | No | Check file naming conventions: number prefix matches chapter_position, all 3 files exist per chapter |

**Note:** At least one of `--check-chapters`, `--check-concepts`, or `--check-conventions` must be specified.

> **IMPORTANT:** Before uploading to Supabase, run `--check-concepts` and fix ALL concept mismatches. Missing concepts will not be linked in `bank_questions_concepts_maps`, breaking the question-to-concept relationship. Either:
> 1. Add the missing concept to the CSV, or
> 2. Update the concept name in the JSON to match an existing concept (use suggestions as hints)

## Prompt Files

Each builder command requires a `--prompt_file_path` argument pointing to a text file containing the extraction prompt. Example prompts are in the `prompts/` directory.

## Directory Structure

```
data/
├── rbse/                          # Input directory (PDFs)
│   └── maths_6_corodova/          # Subject folder
│       ├── 01_knowing_numbers.pdf
│       ├── 02_whole_numbers.pdf
│       └── ...
output/
└── maths_6/                       # Output directory (generated files)
    ├── 01_knowing_numbers_concepts.csv
    ├── 01_knowing_numbers_solved_examples.json
    ├── 01_knowing_numbers_exercise_questions.json
    └── ...
prompts/
├── maths_6_concepts.txt           # Prompt for concept extraction
├── maths_6_solved.txt             # Prompt for solved examples
└── maths_6_exercises.txt          # Prompt for exercise questions
```

## API Reference

### CLI Arguments

All builder commands accept:
| Argument | Required | Description |
|----------|----------|-------------|
| `--input_dir` | Yes | Directory containing chapter PDFs |
| `--output_dir` | Yes | Directory for output CSV/JSON files |
| `--subject_id` | Yes | UUID of the subject for ID generation |
| `--prompt_file_path` | Yes | Path to the prompt text file |

All uploader commands accept:
| Argument | Required | Description |
|----------|----------|-------------|
| `--input_dir` | Yes | Directory containing CSV/JSON files to upload |

## Parallel Processing

The builder scripts (`concepts_builder.py`, `solved_examples_builder.py`, and `exercise_questions_builder.py`) process multiple chapter PDFs in parallel for faster throughput. The maximum number of chapters processed concurrently is controlled by the `MAX_CONCURRENT_GENERATIONS` environment variable (default: 3). This can be set in your `.env` file:

```
MAX_CONCURRENT_GENERATIONS=3
```

- If you want to limit resource usage (e.g., API rate limits), lower this value.
- For maximum speed (if your API quota and machine allow), increase it.

**Example:**

```bash
MAX_CONCURRENT_GENERATIONS=5 python concepts_builder.py \
    --input_dir ./data/rbse/maths_6_corodova \
    --output_dir ./output/maths_6 \
    --subject_id 11ea3956-d46e-4476-bb2c-a50afa027f5c \
    --prompt_file_path ./prompts/maths_6_concepts.txt
```

The scripts will log how many chapters are processed in parallel. All error handling and output remain unchanged.

## Troubleshooting

### "GEMINI_API_KEY not set"

Ensure your `.env` file exists and contains a valid API key.

### "Concepts CSV file not found"

Run `concepts_builder.py` before `exercise_questions_builder.py` or `solved_examples_builder.py`. Questions need concepts to map to.

### "Invalid subject_id UUID"

The `--subject_id` must be a valid UUID. Get it from your database after creating the subject record.

### Upload failures

Check that your Supabase is running and credentials are correct in `.env`.

## Architecture

```
concepts_builder/
├── concepts_builder.py          # CLI: PDF → Concepts CSV
├── exercise_questions_builder.py # CLI: PDF → Exercise JSON
├── solved_examples_builder.py   # CLI: PDF → Solved Examples JSON
├── concepts_uploader.py         # CLI: CSV → Supabase
├── exercise_questions_uploader.py # CLI: JSON → Supabase
├── solved_examples_uploader.py  # CLI: JSON → Supabase
├── boards.py                    # CLI: Add/get board records in Supabase
├── school_class.py              # CLI: Add/get school_class records in Supabase
├── subject.py                   # CLI: Add/get subject records in Supabase
├── generate_school_class_id.py  # CLI: board_id + school_class_name → school_class_id
├── generate_subject_id.py       # CLI: school_class_id + subject_name → subject_id
├── migrate_add_uuids.py         # CLI: Add UUIDs to legacy files
├── verify_concept_exercise_solved_example.py  # CLI: Verify CSV/JSON consistency
├── config.py                    # Settings and logging
├── agents/                      # AI-powered generators (Gemini)
│   ├── base.py                  # Shared Gemini client utilities
│   ├── concept_generator.py
│   ├── solved_examples_generator.py
│   └── exercise_questions_generator.py
├── pipelines/                   # Workflow orchestration
│   ├── concept_pipeline.py
│   ├── questions_pipeline.py
│   └── pdf_pipeline.py
├── schemas/                     # Pydantic models & converters
│   ├── concept_schema.py
│   ├── chapter_to_csv.py
│   └── bank_questions/          # Question bank models
├── prompts/                     # AI prompts (examples)
│   └── rbse/
└── utils/                       # Utilities
    ├── paths.py
    ├── uuid_generator.py        # Deterministic UUID5 generation
    ├── prompt_loader.py         # Load prompts from files
    └── add_uuids_to_existing.py # Add UUIDs to legacy files
