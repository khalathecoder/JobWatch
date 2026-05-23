"""
Location filtering — remote nationwide OR within ~50 miles of Cleveland Heights OH
"""

REMOTE_KEYWORDS = [
    'remote', 'work from home', 'wfh', 'work-from-home',
    'anywhere', 'virtual', 'distributed', 'fully remote',
    'remote-first', 'remote first', 'home office',
    'telecommute', 'telework'
]

# Cities/areas within ~50 miles of Cleveland Heights 44118
CLEVELAND_AREA = [
    'cleveland', 'cleveland heights', 'shaker heights', 'beachwood',
    'independence', 'parma', 'strongsville', 'westlake', 'rocky river',
    'lakewood', 'euclid', 'mentor', 'willoughby', 'solon', 'aurora',
    'hudson', 'stow', 'cuyahoga falls', 'akron', 'barberton',
    'kent', 'ravenna', 'medina', 'brunswick', 'elyria', 'lorain',
    'sandusky', 'painesville', 'chardon', 'geauga',
    'cuyahoga', 'summit', 'lorain county', 'lake county',
    'portage county', 'northeast ohio', 'greater cleveland',
    # State-level (ohio jobs are likely commutable OR hybrid)
    ', oh', ',oh', 'ohio',
]

# Broad US indicators — let through, Claude scores for remote specifics  
US_INDICATORS = [
    'united states', 'nationwide', 'us only', 'u.s.', 'usa',
    'multiple locations', 'various locations', 'flexible'
]

def location_qualifies(location_str):
    """
    Returns (qualifies: bool, reason: str)
    True if job is remote anywhere in US OR physically near Cleveland.
    """
    if not location_str or location_str.strip() in ('', 'See listing', 'N/A'):
        return True, 'unknown location — letting through'

    loc = location_str.lower().strip()

    # Remote → always include
    for kw in REMOTE_KEYWORDS:
        if kw in loc:
            return True, f'remote ({kw})'

    # Cleveland area → include
    for area in CLEVELAND_AREA:
        if area in loc:
            return True, f'Cleveland area ({area})'

    # Broad US → let through for Claude to evaluate
    for us in US_INDICATORS:
        if us in loc:
            return True, f'US-based ({us})'

    # Specific non-Ohio US city → exclude
    return False, f'not remote or local: {location_str}'

def is_clearly_irrelevant_title(title):
    """
    Catch obvious false positives BEFORE hitting Claude.
    The 'Electrical Support Engineer' problem.
    """
    title_lower = title.lower()

    # Hard disqualifiers — non-SW engineering disciplines
    NON_SW = [
        'electrical engineer', 'electrical support', 'electrical technician',
        'civil engineer', 'mechanical engineer',
        'hvac', 'facilities', 'construction', 'manufacturing engineer',
        'process engineer', 'chemical engineer', 'environmental engineer',
        'field service', 'hardware engineer', 'embedded systems',
        'automotive engineer', 'structural engineer', 'controls engineer',
        'instrumentation', 'biomedical engineer', 'lab technician',
        'medical device', 'clinical engineer', 'rf engineer',
        'telecommunications engineer', 'telecom engineer',
    ]
    for term in NON_SW:
        if term in title_lower:
            return True, f'non-SW discipline: {term}'

    # Seniority disqualifiers
    SENIOR_TITLES = [
        'chief ', 'ciso', ' cto ', 'cto,', ' cio ', 'vp ', 'vice president',
        'svp', 'evp', 'director of', 'senior director',
        'managing director', 'principal engineer', 'staff engineer',
        'distinguished engineer', 'fellow,'
    ]
    for term in SENIOR_TITLES:
        if term in title_lower:
            return True, f'too senior: {term}'

    return False, ''
