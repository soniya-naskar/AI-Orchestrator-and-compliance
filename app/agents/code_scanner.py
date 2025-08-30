import re
def scan_code_snippet(snippet: str):
    issues = []
    if not snippet:
        return issues
    if 'allow_weak_mfa' in snippet or 'disable_mfa' in snippet:
        issues.append({'check':'weak_mfa_setting','detail':'found allow_weak_mfa or disable_mfa flag'})
    if re.search(r'password\s*=\s*\"\w+\"', snippet):
        issues.append({'check':'hardcoded_password','detail':'hardcoded password found'})
    return issues
