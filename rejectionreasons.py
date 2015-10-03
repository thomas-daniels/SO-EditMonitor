vandalism = "This edit defaces the post in order to promote a product or service, or is deliberately destructive."
no_improvement = "This edit does not make the post even a little bit easier to read, easier to find, more accurate or more accessible. Changes are either completely superfluous or actively harm readability."
irrelevant_tags = "This edit introduces tags that do not help to define the topic of the question. Tags should help to describe what the question is about, not just what it contains."
intent_conflict = "This edit deviates from the original intent of the post. Even edits that must make drastic changes should strive to preserve the goals of the post's owner."
reply = "This edit was intended to address the author of the post and makes no sense as an edit. It should have been written as a comment or an answer."


def get_reason_type(rejection_reason):
    if rejection_reason == vandalism:
        return "vandalism"
    elif rejection_reason == no_improvement:
        return "no_improvement"
    elif rejection_reason == irrelevant_tags:
        return "irrelevant_tags"
    elif rejection_reason == intent_conflict:
        return "intent_conflict"
    elif rejection_reason == reply:
        return "reply"
    else:
        return "custom"
