# Day 1: Python basics, explained for a JavaScript developer.
# Run it with:  uv run python learn/day01_about_me.py

# --- Variables: no let/const, no semicolons. The type comes from the value. ---
name = "Anamul Hasan"
title = "full-stack software developer"
school = "Georgia Tech"

# --- Lists: like JavaScript arrays ---
skills = ["React", "Next.js", "TypeScript", "Node.js", "Express", "MongoDB", "Tailwind CSS"]
learning = ["Python", "FastAPI", "RAG", "LangGraph", "AWS"]

# --- Dictionaries: like JavaScript objects, but keys are in quotes ---
degree = {
    "school": school,
    "program": "MS in Computer Science",
    "focus": "Artificial Intelligence",
    "graduating": 2027,
}

# --- f-strings: like JavaScript template literals (`Hi ${name}`) ---
print(f"Hi, I am {name}, a {title}.")
print(f"I am studying {degree['program']} at {degree['school']}, focused on {degree['focus']}.")

# len() counts items, like skills.length in JavaScript
# ", ".join(list) is like list.join(", ") in JavaScript
print(f"I work with {len(skills)} main tools: {', '.join(skills)}")

# --- Loops: no braces. The indented lines (4 spaces) are the loop body. ---
for topic in learning:
    print(f"  Currently learning: {topic}")


# --- Functions: 'def' instead of 'function', and a colon plus indentation instead of { } ---
def describe(skill):
    # if / elif / else, like if / else if / else in JavaScript
    if skill in skills:          # 'in' checks whether a list contains it, like skills.includes(skill)
        return f"{skill}: I use it in real projects"
    elif skill in learning:
        return f"{skill}: learning it this month"
    else:
        return f"{skill}: not yet"


print()  # an empty line
for skill in ["React", "Python", "Kotlin"]:
    print(describe(skill))
