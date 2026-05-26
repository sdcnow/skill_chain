from pathlib import Path
from skillchain.core.skill import Skill

_SKILLS_DIR = Path(__file__).parent

read_file = Skill.from_directory(str(_SKILLS_DIR / "read-file"))
write_file = Skill.from_directory(str(_SKILLS_DIR / "write-file"))
list_files = Skill.from_directory(str(_SKILLS_DIR / "list-files"))
summarize = Skill.from_directory(str(_SKILLS_DIR / "summarize"))
extract_json = Skill.from_directory(str(_SKILLS_DIR / "extract-json"))
classify = Skill.from_directory(str(_SKILLS_DIR / "classify"))

__all__ = [
    "read_file",
    "write_file",
    "list_files",
    "summarize",
    "extract_json",
    "classify",
]
