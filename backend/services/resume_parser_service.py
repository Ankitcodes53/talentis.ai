# services/resume_parser_service.py
"""
Resume parsing service using OpenAI for structured data extraction
"""
import os
import json
from openai import OpenAI

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


async def extract_text_from_file(path: str) -> str:
    """Extract text from file (fallback: raw read and decode)"""
    try:
        with open(path, "rb") as f:
            raw = f.read()
        return raw.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""


async def parse_resume_and_extract_fields(path: str) -> dict:
    """
    Parse resume using OpenAI and extract structured fields
    Returns dict with: headline, location, education, experience, skills, certifications, summary
    """
    if not client:
        # Fallback if no OpenAI key
        return {
            "headline": None,
            "location": None,
            "education": [],
            "experience": [],
            "skills": [],
            "certifications": [],
            "summary": None
        }
    
    text = await extract_text_from_file(path)
    
    prompt = f"""You are a precise resume parser. Extract JSON only with these keys:
- headline (string): Professional title/headline
- location (string): Current location
- education (array): List of objects with {{school, degree, field, start_year, end_year}}
- experience (array): List of objects with {{company, title, start_year, end_year, description}}
- skills (array): List of skill strings
- certifications (array): List of certification strings
- summary (string): Brief professional summary

Resume text:
\"\"\"{text[:20000]}\"\"\"

Return only valid JSON. If a field is not present, return null or empty list.
Do not include any explanatory text, only the JSON object.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using more affordable model
            messages=[
                {"role": "system", "content": "You are a resume parser that returns only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON from markdown code blocks if present
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].split("```")[0].strip()
        
        parsed = json.loads(content)
        return parsed
        
    except Exception as e:
        print(f"Error parsing resume with OpenAI: {e}")
        # Graceful fallback: minimal structure
        return {
            "headline": None,
            "location": None,
            "education": [],
            "experience": [],
            "skills": [],
            "certifications": [],
            "summary": None
        }
