# Concepts Builder

A CLI tool for extracting structured educational content from textbook PDFs using AI. Generates concepts, solved examples, and exercise questions with deterministic UUIDs, then uploads them to a Supabase database.

## Overview

This tool provides CLI commands for the content extraction pipeline:

### ID Generation Commands
- **`generate_school_class_id.py`** - Generate school_class UUID from board_id + school_class_name
- **`generate_subject_id.py`** - Generate subject UUID from school_class_id + subject_name

### Database Record Commands (Create in Supabase)
- **`add_school_class.py`** - Create school_class record in Supabase with deterministic UUID
- **`add_subject.py`** - Create subject record in Supabase with deterministic UUID

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

### Add School Class (to Supabase)

Create a school_class record in Supabase with a deterministic UUID:

```bash
python add_school_class.py \
    --board_id 550e8400-e29b-41d4-a716-446655440000 \
    --school_class_name "Class 6" \
    --position 6
```

**Output:**
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
| `--board_id` | Yes | Board UUID (must exist in Supabase) |
| `--school_class_name` | Yes | Class name (e.g., "Class 6", "Class 10") |
| `--position` | Yes | Position/order of the class (e.g., 6 for Class 6) |

### Add Subject (to Supabase)

Create a subject record in Supabase with a deterministic UUID:

```bash
python add_subject.py \
    --school_class_id 7cd86129-fb77-5fae-829a-3a4ec87c1669 \
    --subject_name "Mathematics"
```

**Output:**
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
| `--school_class_id` | Yes | School class UUID (must exist in Supabase) |
| `--subject_name` | Yes | Subject name (e.g., "Mathematics", "Science") |

### Step 1: Generate Concepts

Extract chapter → topic → concept hierarchy from PDFs:

```bash
python concepts_builder.py \
    --input_dir ./data/rbse/maths_6_corodova \
    --output_dir ./output/maths_6 \
    --subject_id 11ea3956-d46e-4476-bb2c-a50afa027f5c \
    --prompt_file_path ./prompts/maths_6_concepts.txt
```

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

# Check file naming conventions and position consistency
python verify_concept_exercise_solved_example.py \
    --input_dir ./output/maths_6 \
    --check-conventions

# Run all checks
python verify_concept_exercise_solved_example.py \
    --input_dir ./output/maths_6 \
    --check-chapters --check-concepts --check-conventions
```

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
├── add_school_class.py          # CLI: Create school_class in Supabase
├── add_subject.py               # CLI: Create subject in Supabase
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
```
