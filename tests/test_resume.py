"""Tests for resume.py."""

from anamul_ai.resume import remove_past_dates


def test_past_jobs_show_no_dates():
    assert remove_past_dates("Software Developer — Jan 2020 – Jun 2022") == "Software Developer"
    assert remove_past_dates("Acme Corp | Springfield, MN | Hybrid Jan 2020 - Jun 2022") == "Acme Corp | Springfield, MN | Hybrid"


def test_current_jobs_keep_present():
    assert remove_past_dates("My Website | example.com August 2024 – Present") == "My Website | example.com August 2024 – Present"
