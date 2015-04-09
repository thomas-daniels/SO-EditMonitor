import re


def check_spam(summary):
    reasons = []
    link_regex = "<a\\s+href\\s*=\\s*[\"']https?://[^\"']+[\"']\\s*>.+?</a>"
    if re.compile(link_regex).search(summary):
        reasons.append("Link in summary")
    return reasons
