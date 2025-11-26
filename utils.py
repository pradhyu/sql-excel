import re

def sanitize_identifier(name):
    """
    Sanitizes a string to be a valid SQL identifier.
    Replaces spaces and special characters with underscores.
    """
    if not name:
        return "unknown"
    
    # Replace non-alphanumeric characters (except underscore) with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    
    # Ensure it doesn't start with a digit
    if sanitized and sanitized[0].isdigit():
        sanitized = '_' + sanitized
        
    return sanitized
