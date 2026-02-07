# Concepts Builder

A tool for extracting structured educational content from textbook PDFs using AI. Generates concepts, solved examples, and exercise questions, then uploads them to a Supabase database.

## Overview

This pipeline processes textbook chapter PDFs through 5 stages:

1. **Concept Extraction** → CSV files with chapter → topic → concept hierarchy
2. **Solved Examples Extraction** → JSON files with worked examples mapped to concepts
3. **Exercise Questions Extraction** → JSON files with practice problems mapped to concepts
4. **PDF Generation** → Review PDFs to verify extraction quality
5. **Upload to Supabase** → Push verified content to the database

## Prerequisites

- **Python 3.11+**
- **uv** - Python package manager ([install guide](https://github.com/astral-sh/uv))
- **Gemini API Key** - For AI-powered content extraction
- **Local Supabase** - Running instance from `skolist-db` repo

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

Optional settings:

| Variable                     | Default            | Description                  |
| ---------------------------- | ------------------ | ---------------------------- |
| `GEMINI_MODEL`               | `gemini-2.5-flash` | Model to use for extraction  |
| `MAX_CONCURRENT_UPLOADS`     | `1`                | Parallel uploads to Supabase |
| `MAX_CONCURRENT_GENERATIONS` | `3`                | Parallel AI extractions      |

## Data Directory Structure

```
data/
├── rbse/                          # Input directory (PDFs)
│   └── maths_6_corodova/          # Subject folder
│       ├── 01_knowing_numbers.pdf
│       ├── 02_whole_numbers.pdf
│       └── ...
└── rbse_output/                   # Output directory (generated files)
    └── maths_6_corodova/
        ├── 01_knowing_numbers_concepts.csv
        ├── 01_knowing_numbers_solved_examples.json
        ├── 01_knowing_numbers_exercise_questions.json
        ├── 01_knowing_numbers_solved_examples.pdf
        └── ...
```

## Pipeline Workflow

### Step 1: Generate Concepts

Extracts chapter → topic → concept hierarchy from PDFs:

```python
# In main.py, uncomment:
await generate_concepts_for_all_chapters()
```

**Output:** `{chapter_name}_concepts.csv`

### Step 2: Generate Solved Examples

Extracts worked examples with solutions, mapped to concepts:

```python
# In main.py, uncomment:
await generate_solved_examples_for_all_chapters()
```

**Output:** `{chapter_name}_solved_examples.json`

### Step 3: Generate Exercise Questions

Extracts practice problems, mapped to concepts:

```python
# In main.py, uncomment:
await generate_exercise_questions_for_all_chapters()
```

**Output:** `{chapter_name}_exercise_questions.json`

### Step 4: Generate Review PDFs

Creates readable PDFs for quality verification:

```python
# In main.py, uncomment:
await generate_pdfs_for_all_chapters()
```

**Output:** `{chapter_name}_solved_examples.pdf`, `{chapter_name}_exercise_questions.pdf`

### Step 5: Upload to Supabase

Uploads verified content to the database:

```python
# In main.py, uncomment:
await upload_to_supabase(question_type="both")  # or "solved" or "exercise"
```

## Running the Pipeline

```bash
# Run the main entry point
uv run python main.py
```

Edit `main.py` to:

1. Set `SUBJECT_NAME` to your subject folder name
2. Optionally set `CHAPTERS_TO_PROCESS` to limit which chapters to process
3. Uncomment the pipeline stage(s) you want to run

## Adding New Subjects

### 1. Create input folder

```bash
mkdir -p data/rbse/your_subject_name
# Copy chapter PDFs into this folder
```

### 2. Create prompts

Add prompt files in `prompts/rbse/` (or appropriate board folder):

```python
# prompts/rbse/your_subject.py

YOUR_SUBJECT_PROMPT = """
Instructions for concept extraction...
"""

YOUR_SUBJECT_SOLVED_EG_PROMPT = """
Instructions for solved examples extraction...
"""

YOUR_SUBJECT_EXERCISE_PROMPT = """
Instructions for exercise questions extraction...
"""
```

### 3. Register subject ID

Add the subject UUID mapping in `config.py`:

```python
SUBJECT_IDS = {
    "your_subject_name": "uuid-from-database",
}
```

### 4. Update main.py

```python
SUBJECT_NAME = "your_subject_name"

# Import your prompts
from prompts.rbse import YOUR_SUBJECT_PROMPT, ...
```

## Architecture

```
concepts_builder/
├── main.py              # Entry point, orchestrates pipeline
├── config.py            # Settings, logging, subject IDs
├── agents/              # AI-powered generators (Gemini)
│   ├── base.py          # Shared Gemini client utilities
│   ├── concept_generator.py
│   ├── solved_examples_generator.py
│   └── exercise_questions_generator.py
├── pipelines/           # Workflow orchestration
│   ├── concept_pipeline.py
│   ├── questions_pipeline.py
│   ├── pdf_pipeline.py
│   └── upload_pipeline.py
├── schemas/             # Pydantic models & converters
│   ├── concept_schema.py
│   ├── chapter_to_csv.py
│   └── bank_questions/  # Question bank models
├── prompts/             # AI prompts by board/subject
│   └── rbse/
└── utils/               # Path utilities
    └── paths.py
```

## Troubleshooting

### "GEMINI_API_KEY not set"

Ensure your `.env` file exists and contains a valid API key.

### "Concepts CSV file not found"

Run Step 1 (concept generation) before Steps 2-3. Questions need concepts to map to.

### "Subject not found in SUBJECT_IDS"

Add your subject's UUID to `config.py` after creating it in the database.

### Upload failures

Check that your local Supabase is running (`supabase start` in `skolist-db`).
