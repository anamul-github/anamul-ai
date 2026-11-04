"""Day 3: turn my resume PDF into clean Markdown for the chatbot.

The PDF stays on my computer because it has my phone number. Only the cleaned
Markdown goes in data/, and this repo is public.
Run it with:  uv run python -m anamul_ai.resume ~/Desktop/Anamul-Hasan-Resume.pdf
"""

import re  # Regular expressions, like JavaScript's /pattern/ and str.replace(/.../g)
import sys  # sys.argv holds the command-line arguments, like process.argv in Node
from pathlib import Path

from pypdf import PdfReader  # Reads text out of PDF files

from anamul_ai.collect import front_matter  # Reuse Day 2's header; importing collect doesn't run its main()

OUTPUT = Path("data/profile/resume.md")
SECTIONS = {"SUMMARY", "WORK EXPERIENCE", "SKILL HIGHLIGHTS", "CERTIFICATIONS", "EDUCATION"}  # A set: fast "is it in here?" checks
PHONE = re.compile(r"\(?\d{3}\)?[\s.-]*\d{3}[\s.-]+\d{4}")  # Matches (555) 123-4567, 555-123-4567 and 555.123.4567
LINK_LABELS = {"LinkedIn", "GitHub", "Website"}  # Clickable in the PDF, but only the word survives as text


def pdf_lines(path: Path) -> list[str]:
    """Read every printed line of the PDF, with extra spaces removed."""
    lines = []
    for page in PdfReader(path).pages:
        # "layout" mode keeps each printed line together; the default mode put every word on its own line
        for line in page.extract_text(extraction_mode="layout").splitlines():
            line = re.sub(r"\s+", " ", line).strip()  # Collapse runs of spaces into one
            if line:
                lines.append(line)
    return lines


def remove_private(line: str) -> str:
    """Drop the phone number and the bare link labels from a line like the contact line."""
    parts = [part.strip() for part in line.split("|")]
    return " | ".join(part for part in parts if not PHONE.search(part) and part not in LINK_LABELS)


def to_markdown(lines: list[str]) -> str:
    out = []
    section = ""
    for line in lines:
        line = remove_private(line)
        if line in SECTIONS:
            section = line
            out += ["", f"## {line.capitalize()}", ""]  # "WORK EXPERIENCE" becomes "## Work experience"
        elif line.startswith("●"):
            out.append("- " + line.removeprefix("●").strip())
        elif out and out[-1].startswith("- ") and not out[-1].endswith("."):
            out[-1] += " " + line  # The PDF wrapped this bullet onto a second line, so join them back
        elif section == "WORK EXPERIENCE" and re.search(r"\d{4}", line):
            # A line with a year: the company line has "|" in it, the job title line doesn't
            level = "###" if "|" in line else "####"
            out += ["", f"{level} {line}", ""]
        else:
            out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out))  # Two headings in a row left extra blank lines


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: uv run python -m anamul_ai.resume path/to/resume.pdf")
    pdf = Path(sys.argv[1]).expanduser()  # expanduser() turns ~ into /Users/anamulhasan
    body = to_markdown(pdf_lines(pdf))

    # Safety check: this file goes to a public repo, so stop if a phone number slipped through
    if PHONE.search(body):
        sys.exit("Found a phone number in the resume text, so nothing was saved.")

    header = front_matter("Anamul Hasan's resume", "resume", "https://www.linkedin.com/in/anamul-hasan")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(f"{header}\n\n# Anamul Hasan's resume\n\n{body.strip()}\n", encoding="utf-8")
    print(f"saved {OUTPUT} ({len(body.split())} words)")


if __name__ == "__main__":
    main()
