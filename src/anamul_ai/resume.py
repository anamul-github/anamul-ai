"""Turn my resume PDF into clean Markdown in data/profile/resume.md, without my phone number.

The PDF stays on my computer. Only the cleaned Markdown is committed, because this repo is public.
Run: uv run python -m anamul_ai.resume ~/Desktop/Anamul-Hasan-Resume.pdf
"""

import re
import sys
from pathlib import Path

from pypdf import PdfReader

from anamul_ai.collect import front_matter

OUTPUT = Path("data/profile/resume.md")
SECTIONS = {"SUMMARY", "WORK EXPERIENCE", "SKILL HIGHLIGHTS", "CERTIFICATIONS", "EDUCATION"}
PHONE = re.compile(r"\(?\d{3}\)?[\s.-]*\d{3}[\s.-]+\d{4}")  # (555) 123-4567, 555-123-4567 or 555.123.4567
LINK_LABELS = {"LinkedIn", "GitHub", "Website"}  # Clickable in the PDF, but only the bare word survives as text
# A finished date range like "Jan 2020 - Jun 2022", with the separator before it; "Present" ranges don't match
DATE_RANGE = re.compile(r"\s*[—|]?\s*[A-Z][a-z]+ \d{4}\s*[-–]\s*[A-Z][a-z]+ \d{4}")
# The PDF's summary counts professional years only; the bot describes total years, the way my profile does
SUMMARY_FROM = "with 3+ years of experience building and supporting enterprise web applications"
SUMMARY_TO = "with 7+ years of experience building software, including professional work building and supporting enterprise web applications"


def pdf_lines(path: Path) -> list[str]:
    """Every printed line of the PDF, with extra spaces removed."""
    lines = []
    for page in PdfReader(path).pages:
        # Layout mode keeps each printed line together; the default put every word on its own line
        for line in page.extract_text(extraction_mode="layout").splitlines():
            line = re.sub(r"\s+", " ", line).strip()
            if line:
                lines.append(line)
    return lines


def remove_private(line: str) -> str:
    """Drop the phone number and the bare link labels from a line like the contact line."""
    parts = [part.strip() for part in line.split("|")]
    return " | ".join(part for part in parts if not PHONE.search(part) and part not in LINK_LABELS)


def remove_past_dates(line: str) -> str:
    """Drop finished date ranges from a job line. My profile covers years of experience instead."""
    return DATE_RANGE.sub("", line).strip()


def to_markdown(lines: list[str]) -> str:
    out = []
    section = ""
    for line in lines:
        line = remove_private(line).replace(SUMMARY_FROM, SUMMARY_TO)
        if line in SECTIONS:
            section = line
            out += ["", f"## {line.capitalize()}", ""]  # "WORK EXPERIENCE" -> "## Work experience"
        elif line.startswith("●"):
            out.append("- " + line.removeprefix("●").strip())
        elif out and out[-1].startswith("- ") and not out[-1].endswith("."):
            out[-1] += " " + line  # The PDF wrapped this bullet onto a second line
        elif section == "WORK EXPERIENCE" and re.search(r"\d{4}", line):
            # A line with a year is either a company line (has "|") or a job title line
            level = "###" if "|" in line else "####"
            out += ["", f"{level} {remove_past_dates(line)}", ""]
        else:
            out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out))  # Two headings in a row leave extra blank lines


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: uv run python -m anamul_ai.resume path/to/resume.pdf")
    pdf = Path(sys.argv[1]).expanduser()
    body = to_markdown(pdf_lines(pdf))

    # This file is public, so refuse to save if a phone number slipped through
    if PHONE.search(body):
        sys.exit("Found a phone number in the resume text, so nothing was saved.")

    header = front_matter("Anamul Hasan's resume", "resume", "https://www.linkedin.com/in/anamul-hasan")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(f"{header}\n\n# Anamul Hasan's resume\n\n{body.strip()}\n", encoding="utf-8")
    print(f"saved {OUTPUT} ({len(body.split())} words)")


if __name__ == "__main__":
    main()
