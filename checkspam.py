import re


def check_spam(summary):
    reasons = []
    link_regex = "<a\\s+href\\s*=\\s*[\"']https?://[^\"']+[\"']\\s*>.+?</a>"
    if re.compile(link_regex, flags=re.IGNORECASE).search(summary):
        reasons.append("Link in summary")
    offensive_regex = "(?i)fuck|shit"
    if re.compile(offensive_regex).search(summary):
        reasons.append("Offensive summary")
    return reasons
