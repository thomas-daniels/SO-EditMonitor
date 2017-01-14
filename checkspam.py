import re


def check_spam(summary):
    reasons = []
    link_regex = "<a\\s+href\\s*=\\s*[\"']https?://[^\"']+[\"']\\s*>.+?</a>"
    if re.compile(link_regex, flags=re.IGNORECASE).search(summary):
        reasons.append("Link in summary")
    offensive_regex = ur"(?is)\b(ur mom|(yo)?u suck|8={3,}D|nigg[aeu][rh]?|(ass ?|a|a-)hole|fag(got)?|daf[au][qk]|(?<!brain)(mother|mutha)?fuc?k+(a|ing?|e?(r|d)| off+| y(ou|e)(rself)?| u+|tard)?|shit(t?er|head)|you scum|dickhead|pedo|whore|cunt|cocksucker|ejaculated?|jerk off|cummies|butthurt|(private|pussy) show|lesbo|bitches|(eat|suck)\b.{0,20}\bdick|dee[sz]e? nut[sz])s?\b"
    if re.compile(offensive_regex).search(summary):
        reasons.append("Offensive summary")
    return reasons
