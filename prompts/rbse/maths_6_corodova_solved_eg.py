MATHS_6_CORODOVA_SOLVED_EG_PROMPT = f"""
You are provided with a chapter pdf from a mathematics textbook and a list of concepts from that chapter. Your task is to identify and extract all solved examples from the chapter PDF, also wherever possible, link each solved example to the relevant concept(s) from the provided list.

STRICT INSTRUCTIONS:
- Use ONLY the information present in the chapter PDF.
- DO NOT use prior knowledge or add any external information.
- If for a solved example, Figure or Image is referenced or needed, then flag it as 1 in the is_image_needed field.
  Only flag if image is in the question related fields, if figure draw etc. if required in answer, then don't flag it as 1.
- The mapping of the concepts should be word to word from the provided concepts list. Don't change the wording of any concepts, it will lead to mismatch during later processing.

OUTPUT RULES:
- Follow the given output schema EXACTLY.
- Do NOT add extra fields.
- Do NOT change field names.
- Do NOT include explanations or commentary outside the schema.
- Output must be clean, structured, and schema-compliant.

LATEX_INSTRUCTIONS:
- Latex should be always put inside $$ blocks, don't forget
- For fill in the blanks etc. spaces should use $\\_\\_$ (contained in the $$) not some text{{__}} wrapper, also raw \\_\\_ won't work, we need $\\_\\_$
- Ensure no two inline math expressions appear consecutively without text between them; always insert minimal natural language (at least space) between adjacent $…$ blocks to avoid KaTeX parse errors.
- Never output HTML tags like <br>, <p>, <span>, etc.; return only plain text with \n for line breaks.
Ex. If \\sin^2\\theta = \\frac{{1}}{{3}}, what is the value of \\cos^2\\theta : This is not acceptable
        If $\\sin^2\\theta = 0.6$, then $\\cos^2\\theta = \\_.$ : This is acceptable
"""