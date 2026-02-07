"""
PDF generator for solved examples banks.

Converts SolvedExamplesBank objects to formatted PDF files using
Playwright for HTML-to-PDF rendering with KaTeX math support.
"""

import os
import logging
import asyncio
from typing import Optional


from playwright.async_api import async_playwright

from schemas.bank_questions.question_bank_schema import SolvedExamplesBank, SolvedExample

logger = logging.getLogger(__name__)


async def save_solved_bank_pdf(bank: SolvedExamplesBank, path: str) -> None:
    """
    Generate a PDF from a SolvedExamplesBank object and save it to the given path.
    
    Args:
        bank: The SolvedExamplesBank object containing all solved examples
        path: The file path where the PDF will be saved
    """
    # Ensure directory exists
    base_dir = os.path.dirname(path)
    if base_dir and not os.path.exists(base_dir):
        os.makedirs(base_dir)
        logger.info(f"Created directory: {base_dir}")

    # Generate HTML content
    html_content = generate_solved_bank_html(bank)

    # Convert to PDF using Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        
        await page.pdf(
            path=path,
            format="A4",
            print_background=True,
            margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"}
        )
        await browser.close()
    
    logger.info(f"PDF saved to: {path}")


def save_solved_bank_pdf_sync(bank: SolvedExamplesBank, path: str) -> None:
    """
    Synchronous wrapper for save_solved_bank_pdf.
    """
    asyncio.run(save_solved_bank_pdf(bank, path))


def generate_solved_bank_html(bank: SolvedExamplesBank) -> str:
    """Generate HTML content for the solved examples bank."""
    
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    body { 
        font-family: 'Times New Roman', Times, serif; 
        color: black; 
        line-height: 1.6; 
        padding: 0; 
        margin: 0; 
        -webkit-print-color-adjust: exact;
    }
    
    .page { 
        padding: 0; 
        box-sizing: border-box; 
    }
    
    .header { 
        text-align: center; 
        margin-bottom: 24px;
        border-bottom: 2px solid black;
        padding-bottom: 16px;
    }
    
    .chapter-name { 
        font-size: 24px; 
        font-weight: bold; 
        text-transform: uppercase; 
        letter-spacing: 0.025em;
        margin: 0; 
        line-height: 1.2;
    }
    
    .subtitle {
        font-size: 18px;
        font-weight: 600;
        margin-top: 8px;
        color: #374151;
    }
    
    .question-count {
        font-size: 14px;
        color: #6b7280;
        margin-top: 4px;
    }
    
    .question { 
        margin-bottom: 24px; 
        padding: 16px;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        background: #fafafa;
        page-break-inside: avoid;
    }
    
    .q-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
    }
    
    .q-number { 
        font-weight: 700; 
        font-size: 16px;
        color: #1f2937;
    }
    
    .q-meta {
        display: flex;
        gap: 12px;
        font-size: 12px;
    }
    
    .q-type {
        background: #3b82f6;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    
    .q-difficulty {
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    
    .q-difficulty.easy { background: #10b981; color: white; }
    .q-difficulty.medium { background: #f59e0b; color: white; }
    .q-difficulty.hard { background: #ef4444; color: white; }
    
    .q-text { 
        font-size: 15px; 
        color: #1f2937;
        margin-bottom: 12px;
    }
    
    .options-grid { 
        display: grid; 
        grid-template-columns: repeat(2, 1fr); 
        gap: 8px 16px; 
        margin: 12px 0;
    }
    
    .option { 
        display: flex; 
        gap: 8px; 
        font-size: 14px;
        padding: 4px 8px;
        background: white;
        border-radius: 4px;
    }
    
    .option.correct {
        background: #d1fae5;
        border: 1px solid #10b981;
    }
    
    .opt-label { 
        font-weight: 600; 
        color: #1f2937;
        min-width: 20px;
    }
    
    .match-table {
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0;
        font-size: 14px;
    }
    
    .match-table th, .match-table td {
        border: 1px solid #d1d5db;
        padding: 8px 12px;
        text-align: left;
    }
    
    .match-table th {
        background: #f3f4f6;
        font-weight: 600;
    }
    
    .answer-section {
        margin-top: 12px;
        padding: 12px;
        background: #ecfdf5;
        border-radius: 6px;
        border-left: 4px solid #10b981;
    }
    
    .ans-label { 
        font-weight: 700; 
        font-size: 14px;
        color: #065f46;
    }
    
    .ans-text {
        font-size: 14px;
        color: #1f2937;
        margin-top: 4px;
    }
    
    .explanation-section {
        margin-top: 8px;
        padding: 12px;
        background: #eff6ff;
        border-radius: 6px;
        border-left: 4px solid #3b82f6;
    }
    
    .exp-label {
        font-weight: 700;
        font-size: 14px;
        color: #1e40af;
    }
    
    .exp-text {
        font-size: 14px;
        color: #1f2937;
        margin-top: 4px;
    }
    
    .concepts-section {
        margin-top: 12px;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    
    .concept-tag {
        background: #e0e7ff;
        color: #3730a3;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .svgs-container {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin: 12px 0;
    }
    
    .q-svg {
        max-width: 100%;
        height: auto;
    }
    
    /* KaTeX */
    .katex { font-size: 1.05em !important; }
    """

    katex_script = """
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            renderMathInElement(document.body, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\\\(', right: '\\\\)', display: false},
                    {left: '\\\\[', right: '\\\\]', display: true}
                ],
                throwOnError: false
            });
        });
    </script>
    """

    questions_html = "".join(
        render_question(q, idx + 1) 
        for idx, q in enumerate(bank.solved_examples_questions)
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
        <style>{css}</style>
    </head>
    <body>
        <div class="page">
            <div class="header">
                <div class="chapter-name">{bank.chapter_name}</div>
                <div class="subtitle">Solved Examples</div>
                <div class="question-count">Total Questions: {len(bank.solved_examples_questions)}</div>
            </div>
            
            {questions_html}
        </div>
        {katex_script}
    </body>
    </html>
    """
    return html


def render_question(q: SolvedExample, display_idx: int) -> str:
    """Render a single question as HTML."""
    
    # Question type and difficulty badges
    q_type = q.question_type or "Unknown"
    difficulty = q.hardness_level or "medium"
    
    # Options rendering for MCQ/MSQ
    options_html = ""
    if q.question_type in ["MCQ4", "MSQ4"]:
        options = [
            (q.option1, 1, q.correct_mcq_option == 1 if q.question_type == "MCQ4" else q.msq_option1_answer),
            (q.option2, 2, q.correct_mcq_option == 2 if q.question_type == "MCQ4" else q.msq_option2_answer),
            (q.option3, 3, q.correct_mcq_option == 3 if q.question_type == "MCQ4" else q.msq_option3_answer),
            (q.option4, 4, q.correct_mcq_option == 4 if q.question_type == "MCQ4" else q.msq_option4_answer),
        ]
        labels = ["a)", "b)", "c)", "d)"]
        options_html = '<div class="options-grid">'
        for i, (opt, num, is_correct) in enumerate(options):
            if opt:
                correct_class = "correct" if is_correct else ""
                options_html += f'<div class="option {correct_class}"><span class="opt-label">{labels[i]}</span> {opt}</div>'
        options_html += '</div>'
    
    # Match the following rendering
    elif q.question_type == "MathTheFollowing" and q.match_columns:
        max_items = max(len(col.items) for col in q.match_columns) if q.match_columns else 0
        options_html = '<table class="match-table">'
        options_html += '<tr>' + ''.join(f'<th>{col.column_name}</th>' for col in q.match_columns) + '</tr>'
        for i in range(max_items):
            options_html += '<tr>'
            for col in q.match_columns:
                item = col.items[i] if i < len(col.items) else ""
                options_html += f'<td>{item}</td>'
            options_html += '</tr>'
        options_html += '</table>'
    
    # True/False rendering
    elif q.question_type == "TrueFalse" and q.istrue is not None:
        options_html = f'<div class="options-grid"><div class="option {"correct" if q.istrue else ""}">True</div><div class="option {"correct" if not q.istrue else ""}">False</div></div>'
    
    # SVG rendering
    svgs_html = ""
    if q.svgs:
        svgs_html = '<div class="svgs-container">'
        for svg in q.svgs:
            if hasattr(svg, 'svg') and svg.svg:
                svgs_html += f'<div class="q-svg">{svg.svg}</div>'
        svgs_html += '</div>'
    elif q.is_image_needed:
        svgs_html = '<div class="svgs-container" style="color: #ef4444; font-weight: 600; font-size: 14px; padding: 12px; border: 1px dashed #ef4444; border-radius: 4px; background: #fee2e2;">[Image/Figure Needed]</div>'
    
    # Answer rendering
    answer_html = ""
    if q.answer_text:
        answer_html = f'''
        <div class="answer-section">
            <span class="ans-label">Answer:</span>
            <div class="ans-text">{q.answer_text}</div>
        </div>
        '''
    
    # Explanation rendering
    explanation_html = ""
    if q.explanation:
        explanation_html = f'''
        <div class="explanation-section">
            <span class="exp-label">Explanation:</span>
            <div class="exp-text">{q.explanation}</div>
        </div>
        '''
    
    # Concepts rendering
    concepts_html = ""
    if q.concepts:
        concepts_html = '<div class="concepts-section">'
        for concept in q.concepts:
            concepts_html += f'<span class="concept-tag">{concept}</span>'
        concepts_html += '</div>'

    html = f"""
    <div class="question">
        <div class="q-header">
            <span class="q-number">Q{display_idx}.</span>
            <div class="q-meta">
                <span class="q-type">{q_type}</span>
                <span class="q-difficulty {difficulty.lower()}">{difficulty.capitalize()}</span>
            </div>
        </div>
        <div class="q-text">{q.question_text or ""}</div>
        {svgs_html}
        {options_html}
        {answer_html}
        {explanation_html}
        {concepts_html}
    </div>
    """
    return html
