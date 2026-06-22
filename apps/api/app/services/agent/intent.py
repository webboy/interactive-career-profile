import re

from app.core.enums import AgentIntent

SKILL_PATTERN = re.compile(r"\b(skill|skills|stack|technology|technologies|expertise)\b", re.IGNORECASE)
EXPERIENCE_PATTERN = re.compile(r"\b(experience|role|worked|employment|career)\b", re.IGNORECASE)
AVAILABILITY_PATTERN = re.compile(r"\b(available|availability|start\s*date|notice\s*period)\b", re.IGNORECASE)
CONTACT_PATTERN = re.compile(r"\b(email|contact|reach\s*you|get\s*in\s*touch)\b", re.IGNORECASE)


def classify_intent(user_message: str) -> tuple[AgentIntent, list[str]]:
    if SKILL_PATTERN.search(user_message):
        return AgentIntent.SKILLS, ["skills"]
    if AVAILABILITY_PATTERN.search(user_message):
        return AgentIntent.AVAILABILITY, ["availability"]
    if EXPERIENCE_PATTERN.search(user_message):
        return AgentIntent.CAREER, ["experience"]
    if CONTACT_PATTERN.search(user_message):
        return AgentIntent.CONTACT, ["contact"]
    return AgentIntent.GENERAL, []
