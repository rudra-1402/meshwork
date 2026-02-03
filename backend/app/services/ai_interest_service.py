import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def detect_interests(user_answers: dict) -> list[str]:
    """
    Returns a list of interest names like:
    ['Technology', 'Design', 'Leadership']
    """

    prompt = f"""
You are an AI career counselor.

Based on the following answers, identify 3–5 main interests.
Choose only from this list:
Technology, Programming, Design, Arts, Business,
Leadership, Teaching, Healthcare, Sports, Research

Answers:
{user_answers}

Return ONLY a comma-separated list.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    interests = response.choices[0].message.content
    return [i.strip() for i in interests.split(",")]
