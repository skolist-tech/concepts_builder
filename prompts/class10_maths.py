"""
This contains the prompt for decomposing a chapter of ncert class 10 maths into concepts.
"""




# NCERT_CLASS_6_SCIENCE = f'''
# You are given an NCERT Class 6 Science chapter PDF.

# The chapter PDF is already structured into clear topics.
# You can directly identify multiple topics in the chapter as headers or sub-headers.

# Your task is to decompose EACH topic into its smallest possible concepts.

# IMPORTANT RULES (STRICT):

# 1. DO NOT apply any external or prior knowledge.
# 2. DO NOT add concepts that are not explicitly present in the chapter PDF.
# 3. ONLY use the information available in the chapter PDF.
# 4. Use paragraphs, sub-headings, examples, activities, diagrams, tables, and definitions
#    present under each topic to identify concepts.
# 5. Concepts are the SMALLEST unit of knowledge in this system.
#    - A concept should represent ONE clear idea, definition, process, fact, or explanation.
# 6. DO NOT merge multiple ideas into one concept.
# 7. DO NOT miss any concept present in the topic.
# 8. If a diagram or activity explains a new idea, it MUST be treated as a separate concept.
# 9. If the same concept appears again for explanation or application, do NOT duplicate it.

# PAGE NUMBER RULES:
# - Assign the page number where the topic or concept FIRST appears in the PDF.
# - Page numbers must be accurate and taken from the PDF.

# OUTPUT RULES:
# - Follow the GIVEN OUTPUT SCHEMA EXACTLY.
# - Do NOT add extra fields.
# - Do NOT change field names.
# - Do NOT include explanations or commentary outside the schema.
# - Output must be clean, structured, and schema-compliant.

# GOAL:
# This output will be used later for:
# - Concept-wise question generation
# - Difficulty-based question paper creation
# - Syllabus mapping and validation

# Accuracy, completeness, and strict adherence to the PDF content are CRITICAL.
# '''

NCERT_GEN = f"""You are given an NCERT textbook chapter PDF.

The chapter is already structured using chapter titles, topics, and sub-topics.
Your task is to extract the content in the following hierarchy:
Chapter → Topics → Concepts.

STRICT INSTRUCTIONS:
- Use ONLY the information present in the chapter PDF.
- DO NOT use prior knowledge or add any external information.
- Identify topics exactly as they appear in the chapter.
- Decompose each topic into the smallest possible concepts.
- A concept must represent ONE clear idea, definition, fact, process, or explanation.
- Use paragraphs, examples, diagrams, tables, activities, and “More to know” boxes to identify concepts.
- DO NOT merge multiple ideas into one concept.
- DO NOT miss any concept present in the chapter.
- DO NOT duplicate concepts even if they are explained again.

PAGE NUMBER RULES:
- Assign the page number where the topic or concept FIRST appears in the PDF.
- Page numbers must be taken strictly from the PDF.

OUTPUT RULES:
- Follow the given output schema EXACTLY.
- Do NOT add extra fields.
- Do NOT change field names.
- Do NOT include explanations or commentary outside the schema.
- Output must be clean, structured, and schema-compliant.

GOAL:
This structured data will be used for concept-wise question generation and exam paper creation.
Accuracy, completeness, and strict adherence to the chapter content are mandatory.
"""
