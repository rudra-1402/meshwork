"""
Questionnaire schema definition and validation.
Validates user responses from the 8-question signup questionnaire.
"""

from app.exceptions import ValidationError


# Expected questionnaire structure
QUESTIONNAIRE_SCHEMA = {
    "q1_project_excitement": {
        "type": "string",
        "required": True,
        "min_length": 30,
        "description": "Describe a coding project that would genuinely excite you"
    },
    "q2_team_roles": {
        "type": "list",
        "required": True,
        "min_items": 1,
        "max_items": 2,
        "allowed_values": [
            "Building core features",
            "Designing architecture",
            "Working on UI/UX",
            "Experimenting with new ideas",
            "Optimizing or fixing things",
            "Leading or coordinating the team",
            "Learning while contributing"
        ],
        "description": "Which role do you naturally gravitate toward in a team?"
    },
    "q2_explanation": {
        "type": "string",
        "required": True,
        "min_length": 20,
        "description": "Explain why you chose those team roles"
    },
    "q3_depth_vs_breadth": {
        "type": "integer",
        "required": True,
        "min": 1,
        "max": 5,
        "description": "Scale 1-5: Specialist vs Generalist"
    },
    "q3_explanation": {
        "type": "string",
        "required": True,
        "min_length": 20,
        "description": "Explain your depth vs breadth choice"
    },
    "q4_problem_solving": {
        "type": "string",
        "required": True,
        "min_length": 20,
        "description": "What do you enjoy most when facing technical problems?"
    },
    "q5_hackathons": {
        "type": "integer",
        "required": True,
        "min": 0,
        "max": 5,
        "description": "Interest in hackathons (0-5)"
    },
    "q5_competitions": {
        "type": "integer",
        "required": True,
        "min": 0,
        "max": 5,
        "description": "Interest in coding competitions (0-5)"
    },
    "q5_team_projects": {
        "type": "integer",
        "required": True,
        "min": 0,
        "max": 5,
        "description": "Interest in long-term team projects (0-5)"
    },
    "q5_open_source": {
        "type": "integer",
        "required": True,
        "min": 0,
        "max": 5,
        "description": "Interest in open source collaboration (0-5)"
    },
    "q5_research": {
        "type": "integer",
        "required": True,
        "min": 0,
        "max": 5,
        "description": "Interest in research or academic projects (0-5)"
    },
    "q6_technologies": {
        "type": "list",
        "required": True,
        "min_items": 1,
        "max_items": 6,
        "allowed_values": [
            "Web (Frontend)",
            "Web (Backend)",
            "Mobile",
            "AI / ML",
            "Data",
            "Systems / Low-level",
            "Cloud / DevOps",
            "Security",
            "Game development",
            "APIs & integrations"
        ],
        "description": "Select up to 6 areas you enjoy or want to explore"
    },
    "q6_explanation": {
        "type": "string",
        "required": False,
        "min_length": 10,
        "description": "Optional: explain one technology choice"
    },
    "q7_collaboration_style": {
        "type": "string",
        "required": True,
        "allowed_values": [
            "I prefer working solo and contributing specific pieces",
            "I enjoy tight collaboration with a small team",
            "I like large, active communities",
            "I enjoy mentoring or helping others grow"
        ],
        "description": "Which collaboration style describes you best?"
    },
    "q7_explanation": {
        "type": "string",
        "required": True,
        "min_length": 15,
        "description": "Explain your collaboration style choice"
    },
    "q8_learning_motivation": {
        "type": "string",
        "required": True,
        "min_length": 20,
        "description": "What motivates you most to code right now?"
    }
}


def validate_questionnaire(data):
    """
    Validate questionnaire data against schema.
    
    Args:
        data: Dict containing user's questionnaire responses
        
    Raises:
        ValidationError: If validation fails with detailed message
        
    Returns:
        True if valid
    """
    if not data or not isinstance(data, dict):
        raise ValidationError("Invalid questionnaire data format")
    
    errors = []
    
    for field_name, rules in QUESTIONNAIRE_SCHEMA.items():
        # Check if required field is present
        if rules.get("required", False) and field_name not in data:
            errors.append(f"Missing required field: {field_name}")
            continue
        
        # Skip optional fields that aren't present
        if not rules.get("required", False) and field_name not in data:
            continue
        
        value = data.get(field_name)
        
        # Type validation
        if rules["type"] == "string":
            if not isinstance(value, str):
                errors.append(f"{field_name} must be a string, got {type(value).__name__}")
                continue
            
            # Check minimum length
            if "min_length" in rules and len(value.strip()) < rules["min_length"]:
                errors.append(
                    f"{field_name} must be at least {rules['min_length']} characters"
                )
            
            # Check allowed values (for categorical strings)
            if "allowed_values" in rules and value not in rules["allowed_values"]:
                errors.append(
                    f"{field_name} must be one of: {rules['allowed_values']}"
                )
        
        elif rules["type"] == "integer":
            if isinstance(value, bool):
                errors.append(f"{field_name} must be an integer, not boolean")
                continue
            if not isinstance(value, int):
                errors.append(f"{field_name} must be an integer, got {type(value).__name__}")
                continue
            
            # Check range
            if "min" in rules and value < rules["min"]:
                errors.append(f"{field_name} must be >= {rules['min']}")
            if "max" in rules and value > rules["max"]:
                errors.append(f"{field_name} must be <= {rules['max']}")
        
        elif rules["type"] == "list":
            if not isinstance(value, list):
                errors.append(f"{field_name} must be a list, got {type(value).__name__}")
                continue
            
            # Check list length
            if "min_items" in rules and len(value) < rules["min_items"]:
                errors.append(f"{field_name} must have at least {rules['min_items']} items")
            if "max_items" in rules and len(value) > rules["max_items"]:
                errors.append(f"{field_name} must have at most {rules['max_items']} items")
            
            # Check allowed values
            if "allowed_values" in rules:
                invalid = [v for v in value if v not in rules["allowed_values"]]
                if invalid:
                    errors.append(
                        f"{field_name} contains invalid values: {invalid}. "
                        f"Allowed: {rules['allowed_values']}"
                    )
    
    if errors:
        raise ValidationError(f"Questionnaire validation failed: {'; '.join(errors)}")
    
    return True


def get_questionnaire_summary(data):
    """
    Generate a human-readable summary of questionnaire responses.
    Useful for logging and debugging.
    
    Args:
        data: Validated questionnaire data
        
    Returns:
        String summary
    """
    summary_parts = [
        f"Team roles: {', '.join(data.get('q2_team_roles', []))}",
        f"Depth/Breadth: {data.get('q3_depth_vs_breadth')}/5",
        f"Technologies: {', '.join(data.get('q6_technologies', [])[:3])}",
        f"Collaboration: {data.get('q7_collaboration_style', 'Not specified')}"
    ]
    return " | ".join(summary_parts)
