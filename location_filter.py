"""
Location and title filters for the job queue.
Pass: fully remote, or within ~50 miles of Cleveland Heights OH.
Fail: explicit onsite-only in a distant city.
Unknown / empty location always passes — we can't filter what we can't see.
"""
import re

# ── Location keywords ─────────────────────────────────────────────────────────
_REMOTE = [
    'remote', 'work from home', 'wfh', 'telecommute', 'virtual',
    'distributed', 'work anywhere', 'fully remote', 'hybrid',
]

_CLEVELAND_AREA = [
    'cleveland', 'ohio', ' oh ', ' oh,', ',oh', 'akron', 'canton',
    'youngstown', 'columbus', 'cincinnati', 'medina', 'strongsville',
    'beachwood', 'solon', 'aurora', 'twinsburg', 'mayfield', 'mentor',
    'elyria', 'lorain', 'parma', 'westlake', 'rocky river', 'bay village',
    'independence', 'valley view', 'warrensville', 'north royalton',
    'berea', 'lakewood', 'euclid', 'willoughby', 'painesville',
]

_ONSITE_ONLY = [
    'on-site only', 'onsite only', 'in-office only', 'no remote',
    'must be local', 'relocation required',
]

# ── Title disqualifiers ───────────────────────────────────────────────────────
_BAD_TITLES = [
    # Physical / trade
    'electrical engineer', 'civil engineer', 'mechanical engineer',
    'hvac', 'facilities engineer', 'hardware engineer',
    'structural engineer', 'field engineer', 'construction',
    'manufacturing engineer', 'plant engineer',
    # Executive — way above level
    ' director', 'vice president', ' vp,', ' vp ', 'ciso', 'chief ',
    'svp', 'evp', 'head of security', 'head of ',
    # Clearly unrelated
    'marketing', 'account executive', 'accountant',
    'customer success', 'customer service', 'administrative assistant',
    'hr manager', 'recruiter', 'talent acquisition',
    # Physical security
    'security guard', 'security officer', 'loss prevention',
    'armed security', 'unarmed security',
]


def location_qualifies(location: str) -> tuple[bool, str]:
    """
    Returns (True, reason) if the location passes the filter.
    Returns (False, reason) if it is clearly out of scope.
    """
    if not location or not location.strip():
        return True, 'location unknown — passed'

    loc = location.lower()

    # Hard fail: explicit onsite-only markers
    for kw in _ONSITE_ONLY:
        if kw in loc:
            return False, f'onsite-only: {kw}'

    # Pass: remote keywords
    for kw in _REMOTE:
        if kw in loc:
            return True, f'remote: {kw}'

    # Pass: Cleveland / Ohio area
    for kw in _CLEVELAND_AREA:
        if kw in loc:
            return True, f'Cleveland area: {kw}'

    # Pass: US-national or vague postings
    if re.search(r'\bus\b|united states|nationwide|multiple locations|anywhere', loc):
        return True, 'US / national'

    # Fail: specific non-Ohio city  ("Dallas, TX" pattern)
    if re.search(r',\s*[A-Z]{2}$', location.strip()):
        state = re.search(r',\s*([A-Z]{2})$', location.strip()).group(1)
        if state not in ('OH',):
            return False, f'specific non-Cleveland city: {location}'

    # Default: pass (ambiguous)
    return True, 'ambiguous — passed'


def is_clearly_irrelevant_title(title: str) -> tuple[bool, str]:
    """
    Returns (True, reason) if the title is obviously NOT a cyber/IT role.
    Returns (False, '') if it should proceed to keyword matching.
    """
    if not title:
        return False, ''

    t = f' {title.lower()} '  # pad with spaces for word-boundary checks

    for kw in _BAD_TITLES:
        if kw in t:
            return True, f'disqualified title: {kw.strip()}'

    return False, ''
