import re

def extract_search_query(message: str):
    """
    Extracts a search query from a user message if it starts with something like:
    'search: ...' or 'find: ...'

    Parameters:
    - message (str): The user's input message

    Returns:
    - str or None: The extracted search query if found, otherwise None
    """
    # Matches phrases like 'search: topic here' or 'find: topic here'
    pattern = r"(?:search|find)[:\-]\s*(.+)"
    match = re.search(pattern, message, re.IGNORECASE)
    
    if match:
        return match.group(1)  # Return just the search term
    return None
