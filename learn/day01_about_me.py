# Day 1: my notes on Python basics, coming from JavaScript.
# Run: uv run python learn/day01_about_me.py

# Variables: no let/const or semicolons; the type comes from the value
name = "Anamul Hasan"
title = "full-stack software developer"
school = "Georgia Tech"

# Lists are like arrays
skills = ["React", "Next.js", "TypeScript", "Node.js", "Express", "MongoDB", "Tailwind CSS"]
learning = ["Python", "FastAPI", "RAG", "LangGraph", "AWS"]

# Dictionaries are like objects, with quoted keys
degree = {
    "school": school,
    "program": "MS in Computer Science",
    "focus": "Artificial Intelligence",
    "graduating": 2027,
}

# f-strings are like template literals
print(f"Hi, I am {name}, a {title}.")
print(f"I am studying {degree['program']} at {degree['school']}, focused on {degree['focus']}.")
print(f"I work with {len(skills)} main tools: {', '.join(skills)}")

# Indentation instead of { }
for topic in learning:
    print(f"  Currently learning: {topic}")


def describe(skill):
    if skill in skills:  # `in` is like .includes()
        return f"{skill}: I use it in real projects"
    elif skill in learning:
        return f"{skill}: learning it this month"
    else:
        return f"{skill}: not yet"


print()
for skill in ["React", "Python", "Kotlin"]:
    print(describe(skill))
