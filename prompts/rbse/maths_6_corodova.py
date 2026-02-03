MATHS_6_CORODOVA_PROMPT = f"""You are given an NCERT textbook chapter PDF.

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

STRUCTURE OF BOOK:
- The Topics in the book are generally in ALL CAPITALS. Use this to help identify topics.
- FOLLOW THIS STRICTLY

"""