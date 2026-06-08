import json
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

client = InferenceClient(
    token=os.getenv("HF_TOKEN")
)

def analyze_resume(resume_text, user_goal):

    prompt = f"""
You are an expert resume reviewer.

Analyze this resume for the target role: {user_goal}

Return ONLY valid JSON in this format:

{{
    "skills": [],
    "missing_skills": [],
    "roadmap": [],
    "interview_questions": []
}}

Resume:
{resume_text}
"""

    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000
        )

        result_text = response.choices[0].message.content.strip()

        result_text = (
            result_text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        print("\n===== RAW AI RESPONSE =====")
        print(result_text)
        print("===========================\n")
        return json.loads(result_text)

    except Exception as e:
        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": str(e)
        }