"""
Custom exceptions for the scoring and proficiency systems.
"""


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


class AlreadyScoredError(Exception):
    """Raised when user attempts to submit questionnaire more than once"""
    pass


class ScoringError(Exception):
    """Raised when AI scoring service fails"""
    pass


class NotScoredError(Exception):
    """Raised when attempting to update scores for user who hasn't completed initial questionnaire"""
    pass


class LanguageProficiencyError(Exception):
    """Raised when language proficiency calculation fails"""
    pass
