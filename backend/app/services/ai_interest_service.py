def detect_interests(answers):
    interests = set()

    if "coding" in answers.get("q1", []):
        interests.add("Software Development")

    if "creative" in answers.get("q1", []):
        interests.add("Design")

    if "tech" in answers.get("q5", []):
        interests.add("Technology")

    if "business" in answers.get("q5", []):
        interests.add("Business")

    if "leader" in answers.get("q6", []):
        interests.add("Leadership")

    if answers.get("q10", ["no"])[0] == "yes":
        interests.add("Startup")

    return list(interests)
