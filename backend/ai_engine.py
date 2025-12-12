"""
AI Engine for Talentis.ai
Handles all AI-powered features including ATS scoring, interview generation, and bias detection.
Uses Grok-3 via XAI API (OpenAI-compatible) with intelligent fallbacks.
"""

import os
import json
import re
from typing import Dict, List, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI


def ats_score(resume_text: str, jd_text: str) -> Dict:
    """
    Score resume match to job description using Grok-3 AI.
    
    Args:
        resume_text: Full text of candidate's resume
        jd_text: Job description text with title, requirements, and skills
    
    Returns:
        {
            "score": 85,  # Match score out of 100
            "explanation": "Candidate has strong Python and FastAPI experience...",
            "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
            "missing_skills": ["AWS", "Kubernetes"],
            "recommendation": "Strong Match"
        }
    """
    try:
        # Initialize Grok-3 model via XAI API (OpenAI-compatible)
        api_key = os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY", "dummy-key")
        base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
        
        llm = ChatOpenAI(
            model="grok-beta",  # Grok-3 model
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Create ATS scoring prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Applicant Tracking System (ATS) analyzer. 
Your job is to objectively score how well a candidate's resume matches a job description.

Analyze the resume against the job description and provide:
1. A match score from 0-100 (be realistic and fair)
2. A detailed explanation of why the candidate is or isn't a good match
3. List of matched skills found in both resume and JD
4. List of missing critical skills from the JD not found in resume
5. Overall recommendation: "Strong Match" (80+), "Good Match" (60-79), "Moderate Match" (40-59), or "Weak Match" (<40)

Consider:
- Technical skills match
- Experience level and years
- Education relevance
- Domain expertise
- Specific tools/frameworks mentioned
- Project complexity and scale

Return ONLY a valid JSON object with this exact structure:
{
  "score": <number 0-100>,
  "explanation": "<detailed analysis>",
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3", "skill4"],
  "recommendation": "<Strong Match|Good Match|Moderate Match|Weak Match>"
}"""),
            ("user", """Job Description:
{jd_text}

---

Candidate Resume:
{resume_text}

---

Analyze this match and return ONLY the JSON object with no additional text.""")
        ])
        
        # Format and send to Grok-3
        messages = prompt.format_messages(
            jd_text=jd_text[:3000],  # Limit JD length
            resume_text=resume_text[:4000]  # Limit resume length
        )
        
        try:
            response = llm.predict_messages(messages)
            result_text = response.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Validate required fields
                required_fields = ['score', 'explanation', 'matched_skills', 'missing_skills', 'recommendation']
                if all(field in result for field in required_fields):
                    # Ensure score is within bounds
                    result['score'] = max(0, min(100, float(result['score'])))
                    return result
                else:
                    raise ValueError("Missing required fields in AI response")
            else:
                raise ValueError("No JSON found in AI response")
                
        except Exception as llm_error:
            print(f"⚠️ Grok-3 API error: {llm_error}")
            # Fallback to keyword-based scoring
            return _fallback_ats_score(resume_text, jd_text)
            
    except Exception as e:
        print(f"⚠️ ATS scoring error: {e}")
        # Ultimate fallback
        return _fallback_ats_score(resume_text, jd_text)


def _fallback_ats_score(resume_text: str, jd_text: str) -> Dict:
    """
    Fallback ATS scoring using keyword matching when AI is unavailable.
    Simple but effective for basic matching.
    """
    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower()
    
    # Extract potential skills from JD (common technical terms)
    common_skills = [
        'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node.js',
        'fastapi', 'django', 'flask', 'express', 'spring',
        'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
        'git', 'ci/cd', 'jenkins', 'github actions',
        'machine learning', 'deep learning', 'tensorflow', 'pytorch',
        'rest api', 'graphql', 'microservices', 'agile', 'scrum'
    ]
    
    # Find skills mentioned in JD
    jd_skills = [skill for skill in common_skills if skill in jd_lower]
    
    # Find matched skills in resume
    matched_skills = [skill for skill in jd_skills if skill in resume_lower]
    missing_skills = [skill for skill in jd_skills if skill not in resume_lower]
    
    # Calculate base score
    if len(jd_skills) > 0:
        skill_match_score = (len(matched_skills) / len(jd_skills)) * 100
    else:
        skill_match_score = 50  # Default if no specific skills found
    
    # Boost score for experience indicators
    experience_keywords = ['years', 'experience', 'led', 'managed', 'developed', 'built', 'designed']
    experience_matches = sum(1 for kw in experience_keywords if kw in resume_lower)
    experience_boost = min(15, experience_matches * 3)
    
    # Education boost
    education_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'computer science']
    education_boost = 10 if any(kw in resume_lower for kw in education_keywords) else 0
    
    # Calculate final score
    final_score = min(100, skill_match_score + experience_boost + education_boost)
    
    # Generate explanation
    matched_count = len(matched_skills)
    total_count = len(jd_skills)
    
    if final_score >= 80:
        recommendation = "Strong Match"
        explanation = f"Excellent match! Found {matched_count} out of {total_count} required skills in resume. Candidate demonstrates strong relevant experience and qualifications."
    elif final_score >= 60:
        recommendation = "Good Match"
        explanation = f"Good fit with {matched_count} out of {total_count} required skills. Candidate has solid foundation with some gaps that could be addressed through training."
    elif final_score >= 40:
        recommendation = "Moderate Match"
        explanation = f"Moderate match with {matched_count} out of {total_count} required skills. Candidate shows potential but may need significant onboarding in missing areas."
    else:
        recommendation = "Weak Match"
        explanation = f"Limited match with only {matched_count} out of {total_count} required skills found. Significant skill gaps exist for this role."
    
    # Add detail about missing skills
    if missing_skills:
        explanation += f" Missing skills include: {', '.join(missing_skills[:5])}."
    
    explanation += " (Note: This is a basic keyword analysis. For more accurate scoring, configure XAI_API_KEY for Grok-3 AI analysis.)"
    
    return {
        "score": round(final_score, 1),
        "explanation": explanation,
        "matched_skills": [skill.title() for skill in matched_skills],
        "missing_skills": [skill.title() for skill in missing_skills],
        "recommendation": recommendation
    }


def generate_interview_questions(job_title: str, skills: List[str], language: str = "en", count: int = 10) -> List[Dict]:
    """
    Generate interview questions using Grok-3 AI.
    
    Args:
        job_title: Job title/position
        skills: List of required skills
        language: Language code (en, es, fr, hi, zh)
        count: Number of questions to generate
    
    Returns:
        List of {"question_id": 1, "question_text": "...", "category": "technical"}
    """
    try:
        api_key = os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY", "dummy-key")
        base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
        
        llm = ChatOpenAI(
            model="grok-beta",
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Create prompt for question generation
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""Generate {count} interview questions for a {job_title} position.
Skills to assess: {', '.join(skills)}
Language: {language}

Return ONLY a JSON array of questions with this structure:
[
  {{"question_id": 1, "question_text": "...", "category": "technical"}},
  {{"question_id": 2, "question_text": "...", "category": "behavioral"}}
]

Categories: technical, behavioral, problem-solving, communication"""),
            ("user", f"Generate {count} interview questions for {job_title}.")
        ])
        
        messages = prompt.format_messages()
        response = llm.predict_messages(messages)
        
        # Parse JSON
        json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
        if json_match:
            questions = json.loads(json_match.group())
            return questions
        else:
            raise ValueError("No JSON array found")
            
    except Exception as e:
        print(f"⚠️ Question generation error: {e}")
        # Fallback to default questions
        return _fallback_interview_questions(job_title, skills, count)


def _fallback_interview_questions(job_title: str, skills: List[str], count: int = 10) -> List[Dict]:
    """Fallback interview questions when AI is unavailable."""
    questions = []
    
    # Technical questions based on skills
    for i, skill in enumerate(skills[:4], 1):
        questions.append({
            "question_id": i,
            "question_text": f"Can you describe your experience with {skill} and provide an example of a project where you used it?",
            "category": "technical"
        })
    
    # Generic behavioral questions
    behavioral = [
        "Tell me about a challenging project you worked on and how you overcame obstacles.",
        "How do you handle tight deadlines and prioritize multiple tasks?",
        "Describe a situation where you had to work with a difficult team member.",
        "What motivates you in your work, and how do you stay productive?",
        "Tell me about a time you had to learn a new technology quickly.",
        "How do you approach debugging complex issues in your code?"
    ]
    
    for i, q in enumerate(behavioral[:count-len(questions)], len(questions)+1):
        questions.append({
            "question_id": i,
            "question_text": q,
            "category": "behavioral"
        })
    
    return questions[:count]


def generate_behavioral_questions(jd_text: str, count: int = 5) -> List[Dict]:
    """
    Generate behavioral interview questions based on job description using Grok-3.
    
    Args:
        jd_text: Full job description text
        count: Number of behavioral questions to generate
    
    Returns:
        List of behavioral questions with situational focus
    """
    try:
        api_key = os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY", "dummy-key")
        base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
        
        llm = ChatOpenAI(
            model="grok-beta",
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.8,
            max_tokens=1500
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert HR interviewer. Generate {count} behavioral interview questions based on the job description.

Use the STAR method framework (Situation, Task, Action, Result).

Questions should:
- Start with "Tell me about a time..." or "Describe a situation..."
- Focus on real scenarios relevant to the job requirements
- Assess soft skills: leadership, teamwork, problem-solving, stress management, conflict resolution
- Be specific to the role's challenges and responsibilities

Return ONLY a JSON array:
[
  {{"question_id": 1, "question_text": "Tell me about a time you...", "category": "behavioral"}},
  {{"question_id": 2, "question_text": "Describe a situation where...", "category": "behavioral"}}
]"""),
            ("user", f"""Job Description:
{jd_text[:2000]}

Generate {count} behavioral interview questions.""")
        ])
        
        messages = prompt.format_messages()
        response = llm.predict_messages(messages)
        
        # Parse JSON
        json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
        if json_match:
            questions = json.loads(json_match.group())
            return questions
        else:
            raise ValueError("No JSON array found")
            
    except Exception as e:
        print(f"⚠️ Behavioral question generation error: {e}")
        # Fallback questions
        return [
            {
                "question_id": i + 1,
                "question_text": q,
                "category": "behavioral"
            }
            for i, q in enumerate([
                "Tell me about a time you handled a stressful situation at work and how you managed it.",
                "Describe a situation where you had to work with a difficult team member. How did you handle it?",
                "Tell me about a time you failed and what you learned from the experience.",
                "Describe a situation where you had to meet a tight deadline. What was your approach?",
                "Tell me about a time you showed leadership even when you weren't in a leadership role."
            ][:count])
        ]


def generate_coding_problems(skills: List[str], difficulty: str = "medium", count: int = 3) -> List[Dict]:
    """
    Generate coding problems based on skills using Grok-3 AI.
    
    Args:
        skills: List of technical skills to test (e.g., ["Python", "Algorithms", "React"])
        difficulty: Problem difficulty - "easy", "medium", or "hard"
        count: Number of problems to generate
    
    Returns:
        List of coding problems with title, description, starter code, test cases
    """
    try:
        api_key = os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY", "dummy-key")
        base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
        
        llm = ChatOpenAI(
            model="grok-beta",
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.7,
            max_tokens=2500
        )
        
        # Map skills to primary language
        language_map = {
            "python": "python3",
            "java": "java",
            "javascript": "nodejs",
            "c++": "cpp17",
            "react": "nodejs",
            "node.js": "nodejs",
            "springboot": "java"
        }
        
        primary_skill = skills[0].lower() if skills else "python"
        language = language_map.get(primary_skill, "python3")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert coding interview problem creator. Generate {count} coding problems for a {difficulty} level assessment.

Skills to test: {', '.join(skills)}
Difficulty: {difficulty}

For {difficulty} level:
- easy: FizzBuzz, palindrome, reverse string, sum array, basic loops
- medium: Two-sum, valid parentheses, binary search, linked list operations
- hard: Dynamic programming, graph algorithms, system design

Return ONLY a JSON array with this exact structure:
[
  {{
    "problem_id": 1,
    "title": "Problem Title",
    "description": "Detailed problem description with examples and constraints",
    "difficulty": "{difficulty}",
    "language": "{language}",
    "starter_code": "def solution():\\n    # Write your code here\\n    pass",
    "test_cases": [
      {{"input": "5", "expected_output": "120"}},
      {{"input": "3", "expected_output": "6"}}
    ]
  }}
]

Make problems relevant to: {', '.join(skills)}"""),
            ("user", f"Generate {count} {difficulty} coding problems for {', '.join(skills)}.")
        ])
        
        messages = prompt.format_messages()
        response = llm.predict_messages(messages)
        
        # Parse JSON
        json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
        if json_match:
            problems = json.loads(json_match.group())
            return problems
        else:
            raise ValueError("No JSON array found")
            
    except Exception as e:
        print(f"⚠️ Coding problem generation error: {e}")
        # Fallback to default problems
        return _fallback_coding_problems(skills, difficulty, count)


def _fallback_coding_problems(skills: List[str], difficulty: str = "medium", count: int = 3) -> List[Dict]:
    """Fallback coding problems when AI is unavailable."""
    
    # Determine language from skills
    primary_skill = skills[0].lower() if skills else "python"
    
    language_map = {
        "python": "python3",
        "java": "java",
        "javascript": "nodejs",
        "c++": "cpp17",
        "react": "nodejs",
        "node.js": "nodejs"
    }
    language = language_map.get(primary_skill, "python3")
    
    # Language-specific templates
    templates = {
        "python3": {
            "easy": {
                "title": "FizzBuzz",
                "description": "Write a function that prints numbers from 1 to n. For multiples of 3, print 'Fizz', for multiples of 5, print 'Buzz', and for multiples of both, print 'FizzBuzz'.\n\nExample:\nInput: n = 15\nOutput: 1, 2, Fizz, 4, Buzz, Fizz, 7, 8, Fizz, Buzz, 11, Fizz, 13, 14, FizzBuzz",
                "starter_code": "def fizzbuzz(n):\n    # Write your code here\n    pass\n\n# Test\nprint(fizzbuzz(15))",
                "test_cases": [
                    {"input": "15", "expected_output": "1, 2, Fizz, 4, Buzz, Fizz, 7, 8, Fizz, Buzz, 11, Fizz, 13, 14, FizzBuzz"},
                    {"input": "5", "expected_output": "1, 2, Fizz, 4, Buzz"}
                ]
            },
            "medium": {
                "title": "Two Sum",
                "description": "Given an array of integers and a target sum, return indices of two numbers that add up to the target.\n\nExample:\nInput: nums = [2, 7, 11, 15], target = 9\nOutput: [0, 1]\nExplanation: nums[0] + nums[1] = 2 + 7 = 9",
                "starter_code": "def two_sum(nums, target):\n    # Write your code here\n    pass\n\n# Test\nprint(two_sum([2, 7, 11, 15], 9))",
                "test_cases": [
                    {"input": "[2, 7, 11, 15], 9", "expected_output": "[0, 1]"},
                    {"input": "[3, 2, 4], 6", "expected_output": "[1, 2]"}
                ]
            },
            "hard": {
                "title": "Valid Parentheses",
                "description": "Given a string containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid. Opening brackets must be closed by the same type in correct order.\n\nExample:\nInput: '({[]})'\nOutput: True",
                "starter_code": "def is_valid(s):\n    # Write your code here\n    pass\n\n# Test\nprint(is_valid('({[]})'))",
                "test_cases": [
                    {"input": "({[]})", "expected_output": "True"},
                    {"input": "([)]", "expected_output": "False"}
                ]
            }
        },
        "java": {
            "easy": {
                "title": "Reverse String",
                "description": "Write a function to reverse a string.\n\nExample:\nInput: 'hello'\nOutput: 'olleh'",
                "starter_code": "public class Solution {\n    public static String reverse(String s) {\n        // Write your code here\n        return \"\";\n    }\n    \n    public static void main(String[] args) {\n        System.out.println(reverse(\"hello\"));\n    }\n}",
                "test_cases": [
                    {"input": "hello", "expected_output": "olleh"},
                    {"input": "world", "expected_output": "dlrow"}
                ]
            }
        },
        "nodejs": {
            "easy": {
                "title": "Array Sum",
                "description": "Write a function that returns the sum of all numbers in an array.\n\nExample:\nInput: [1, 2, 3, 4, 5]\nOutput: 15",
                "starter_code": "function sumArray(arr) {\n    // Write your code here\n}\n\n// Test\nconsole.log(sumArray([1, 2, 3, 4, 5]));",
                "test_cases": [
                    {"input": "[1, 2, 3, 4, 5]", "expected_output": "15"},
                    {"input": "[10, 20, 30]", "expected_output": "60"}
                ]
            }
        }
    }
    
    # Get template for language and difficulty
    lang_templates = templates.get(language, templates["python3"])
    template = lang_templates.get(difficulty, lang_templates.get("medium", lang_templates["easy"]))
    
    # Generate problems
    problems = []
    for i in range(count):
        problems.append({
            "problem_id": i + 1,
            "title": template["title"] + (f" - Variant {i+1}" if i > 0 else ""),
            "description": template["description"],
            "difficulty": difficulty,
            "language": language,
            "starter_code": template["starter_code"],
            "test_cases": template["test_cases"]
        })
    
    return problems


def generate_stress_test(experience_level: str, skills: List[str] = None, count: int = 3) -> Dict:
    """
    Generate timed stress test with DSA problems based on candidate experience level.
    
    Args:
        experience_level: "junior", "mid", "senior" (or years: <2, 2-5, 5+)
        skills: Optional list of skills to focus on
        count: Number of problems (default 3)
    
    Returns:
        {
            "difficulty": "hard",
            "time_limit_minutes": 45,
            "problems": [...],
            "instructions": "Complete within time limit..."
        }
    """
    try:
        # Map experience to difficulty
        experience_map = {
            "junior": {"difficulty": "easy", "time_limit": 20},
            "mid": {"difficulty": "medium", "time_limit": 30},
            "senior": {"difficulty": "hard", "time_limit": 45},
            "entry": {"difficulty": "easy", "time_limit": 20},
            "intermediate": {"difficulty": "medium", "time_limit": 30},
            "advanced": {"difficulty": "hard", "time_limit": 45}
        }
        
        # Default to mid-level if unknown
        config = experience_map.get(experience_level.lower(), experience_map["mid"])
        difficulty = config["difficulty"]
        time_limit = config["time_limit"]
        
        # Use Grok-3 to generate LeetCode-style problems
        api_key = os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY", "dummy-key")
        base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
        
        llm = ChatOpenAI(
            model="grok-beta",
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0.7,
            max_tokens=3000
        )
        
        skill_focus = ', '.join(skills) if skills else "Data Structures and Algorithms"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert at creating LeetCode-style DSA (Data Structures & Algorithms) problems for technical interviews.

Generate {count} {difficulty} level DSA problems for a {experience_level} level candidate.
Focus areas: {skill_focus}

Problem types by difficulty:
- EASY: Two Sum, Palindrome, Reverse String, Valid Parentheses, Merge Sorted Arrays
- MEDIUM: Binary Search, Linked List Cycle, Longest Substring, Valid BST, Clone Graph
- HARD: Merge K Sorted Lists, Trapping Rain Water, Word Ladder, Serialize Tree, LRU Cache

Each problem should:
1. Be a classic DSA problem (similar to LeetCode)
2. Include time/space complexity hints
3. Have clear examples
4. Include edge cases in test cases
5. Have appropriate time expectations ({difficulty} level)

Return ONLY a JSON array:
[
  {{
    "problem_id": 1,
    "title": "Two Sum",
    "description": "Given an array of integers nums and target, return indices of two numbers that add up to target.\\n\\nExample 1:\\nInput: nums = [2,7,11,15], target = 9\\nOutput: [0,1]\\n\\nConstraints:\\n- 2 <= nums.length <= 10^4\\n- Each input has exactly one solution",
    "difficulty": "{difficulty}",
    "language": "python3",
    "time_complexity_hint": "O(n)",
    "space_complexity_hint": "O(n)",
    "estimated_time_minutes": 15,
    "starter_code": "def twoSum(nums, target):\\n    # Write your solution here\\n    pass\\n\\n# Test\\nprint(twoSum([2,7,11,15], 9))",
    "test_cases": [
      {{"input": "[2,7,11,15], 9", "expected_output": "[0, 1]"}},
      {{"input": "[3,2,4], 6", "expected_output": "[1, 2]"}}
    ]
  }}
]"""),
            ("user", f"Generate {count} {difficulty} DSA problems for {experience_level} level focusing on {skill_focus}.")
        ])
        
        messages = prompt.format_messages()
        response = llm.predict_messages(messages)
        
        # Parse JSON
        json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
        if json_match:
            problems = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in response")
            
    except Exception as e:
        print(f"⚠️ Stress test generation error: {e}")
        # Fallback to template problems
        problems = _fallback_stress_test_problems(difficulty, count)
    
    # Calculate total time estimate
    total_time = sum(p.get("estimated_time_minutes", time_limit // count) for p in problems)
    
    return {
        "difficulty": difficulty,
        "time_limit_minutes": time_limit,
        "total_estimated_time": min(total_time, time_limit),
        "experience_level": experience_level,
        "problems": problems,
        "instructions": f"""⏱️ TIMED STRESS TEST - {difficulty.upper()} LEVEL

Time Limit: {time_limit} minutes
Problems: {count}

Instructions:
1. Solve all {count} problems within the time limit
2. Code must pass all test cases to be considered correct
3. Focus on correctness first, then optimization
4. You will be flagged if you exceed the time limit
5. Partial credit given for passing some test cases

Good luck! 🚀""",
        "overtime_penalty": True
    }


def _fallback_stress_test_problems(difficulty: str, count: int = 3) -> List[Dict]:
    """Fallback stress test problems when AI is unavailable."""
    
    templates = {
        "easy": [
            {
                "problem_id": 1,
                "title": "Two Sum",
                "description": """Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

Example 1:
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: nums[0] + nums[1] == 9, so we return [0, 1]

Example 2:
Input: nums = [3,2,4], target = 6
Output: [1,2]

Constraints:
- 2 <= nums.length <= 10^4
- -10^9 <= nums[i] <= 10^9
- Only one valid answer exists""",
                "difficulty": "easy",
                "language": "python3",
                "time_complexity_hint": "O(n)",
                "space_complexity_hint": "O(n)",
                "estimated_time_minutes": 8,
                "starter_code": "def twoSum(nums, target):\n    # Write your solution here\n    pass\n\n# Test\nprint(twoSum([2,7,11,15], 9))",
                "test_cases": [
                    {"input": "[2,7,11,15], 9", "expected_output": "[0, 1]"},
                    {"input": "[3,2,4], 6", "expected_output": "[1, 2]"},
                    {"input": "[3,3], 6", "expected_output": "[0, 1]"}
                ]
            },
            {
                "problem_id": 2,
                "title": "Valid Palindrome",
                "description": """A phrase is a palindrome if, after converting all uppercase letters into lowercase and removing all non-alphanumeric characters, it reads the same forward and backward.

Given a string s, return true if it is a palindrome, or false otherwise.

Example 1:
Input: s = "A man, a plan, a canal: Panama"
Output: true

Example 2:
Input: s = "race a car"
Output: false

Constraints:
- 1 <= s.length <= 2 * 10^5
- s consists only of printable ASCII characters""",
                "difficulty": "easy",
                "language": "python3",
                "time_complexity_hint": "O(n)",
                "space_complexity_hint": "O(1)",
                "estimated_time_minutes": 6,
                "starter_code": "def isPalindrome(s):\n    # Write your solution here\n    pass\n\n# Test\nprint(isPalindrome('A man, a plan, a canal: Panama'))",
                "test_cases": [
                    {"input": "A man, a plan, a canal: Panama", "expected_output": "True"},
                    {"input": "race a car", "expected_output": "False"}
                ]
            }
        ],
        "medium": [
            {
                "problem_id": 1,
                "title": "Longest Substring Without Repeating Characters",
                "description": """Given a string s, find the length of the longest substring without repeating characters.

Example 1:
Input: s = "abcabcbb"
Output: 3
Explanation: The answer is "abc", with length 3.

Example 2:
Input: s = "bbbbb"
Output: 1
Explanation: The answer is "b", with length 1.

Constraints:
- 0 <= s.length <= 5 * 10^4
- s consists of English letters, digits, symbols and spaces""",
                "difficulty": "medium",
                "language": "python3",
                "time_complexity_hint": "O(n)",
                "space_complexity_hint": "O(min(m,n))",
                "estimated_time_minutes": 12,
                "starter_code": "def lengthOfLongestSubstring(s):\n    # Write your solution here\n    pass\n\n# Test\nprint(lengthOfLongestSubstring('abcabcbb'))",
                "test_cases": [
                    {"input": "abcabcbb", "expected_output": "3"},
                    {"input": "bbbbb", "expected_output": "1"},
                    {"input": "pwwkew", "expected_output": "3"}
                ]
            }
        ],
        "hard": [
            {
                "problem_id": 1,
                "title": "Trapping Rain Water",
                "description": """Given n non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.

Example 1:
Input: height = [0,1,0,2,1,0,1,3,2,1,2,1]
Output: 6
Explanation: The above elevation map traps 6 units of rain water.

Example 2:
Input: height = [4,2,0,3,2,5]
Output: 9

Constraints:
- n == height.length
- 1 <= n <= 2 * 10^4
- 0 <= height[i] <= 10^5""",
                "difficulty": "hard",
                "language": "python3",
                "time_complexity_hint": "O(n)",
                "space_complexity_hint": "O(1)",
                "estimated_time_minutes": 20,
                "starter_code": "def trap(height):\n    # Write your solution here\n    pass\n\n# Test\nprint(trap([0,1,0,2,1,0,1,3,2,1,2,1]))",
                "test_cases": [
                    {"input": "[0,1,0,2,1,0,1,3,2,1,2,1]", "expected_output": "6"},
                    {"input": "[4,2,0,3,2,5]", "expected_output": "9"}
                ]
            }
        ]
    }
    
    available = templates.get(difficulty, templates["medium"])
    return available[:count]
