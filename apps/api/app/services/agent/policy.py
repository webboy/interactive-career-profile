import re

from app.core.enums import PolicyDecision

SALARY_PATTERN = re.compile(
    r"\b(salary|salaries|compensation|pay\s*range|payrate|hourly\s*rate|"
    r"annual\s*package|remuneration|wage|wages)\b",
    re.IGNORECASE,
)
PHONE_PATTERN = re.compile(
    r"\b(phone|phone\s*number|mobile|cell\s*number|whatsapp|telegram\s*number|call\s*me)\b",
    re.IGNORECASE,
)
PHONE_NUMBER_PATTERN = re.compile(r"\+?\d[\d\s().-]{7,}\d")


SALARY_REFUSAL = (
    "I cannot discuss salary or compensation. "
    "Please contact the profile owner through approved channels."
)
CONTACT_REFUSAL = (
    "I cannot share phone numbers or private contact details through this assistant."
)
UNSUPPORTED_REFUSAL = (
    "I do not have enough verified public information to answer that question safely."
)
GROUNDING_REFUSAL = (
    "I cannot provide a verified answer because the response could not be grounded "
    "in public profile data."
)


def evaluate_policy(user_message: str) -> PolicyDecision:
    if SALARY_PATTERN.search(user_message):
        return PolicyDecision.REFUSE_SALARY
    if PHONE_PATTERN.search(user_message) or PHONE_NUMBER_PATTERN.search(user_message):
        return PolicyDecision.REFUSE_CONTACT
    return PolicyDecision.ALLOW


def policy_refusal_message(decision: PolicyDecision) -> str:
    if decision == PolicyDecision.REFUSE_SALARY:
        return SALARY_REFUSAL
    if decision == PolicyDecision.REFUSE_CONTACT:
        return CONTACT_REFUSAL
    if decision == PolicyDecision.REFUSE_GROUNDING:
        return GROUNDING_REFUSAL
    return UNSUPPORTED_REFUSAL
