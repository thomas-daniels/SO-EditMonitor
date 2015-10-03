import rejectionreasons


class RestrictedMode():
    def __init__(self, mode):
        if mode > 63:
            raise ValueError("Mode cannot be larger than 63.")
        self.mode = mode
        self.enabled_reasons = []
        if mode & 0b100000 != 0:
            self.enabled_reasons.append("vandalism")
        if mode & 0b010000 != 0:
            self.enabled_reasons.append("no_improvement")
        if mode & 0b001000 != 0:
            self.enabled_reasons.append("irrelevant_tags")
        if mode & 0b000100 != 0:
            self.enabled_reasons.append("intent_conflict")
        if mode & 0b000010 != 0:
            self.enabled_reasons.append("reply")
        if mode & 0b000001 != 0:
            self.enabled_reasons.append("custom")

    def should_report(self, reason):
        return rejectionreasons.get_reason_type(reason) in self.enabled_reasons
