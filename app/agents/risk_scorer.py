def compute_risk(policy_hits, evidence_hits, code_issues):
    score = 0.0
    if any('MFA required' in p['snippet'] for p in policy_hits):
        if any('disabled' in e['snippet'].lower() or 'no mfa' in e['snippet'].lower() for e in evidence_hits):
            score += 70
        elif any('otp' in e['snippet'].lower() or 'sms' in e['snippet'].lower() for e in evidence_hits):
            score += 20
    score += len(code_issues) * 15
    return min(score, 100.0)
