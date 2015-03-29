from user import User


class SuggestedEdit:
    def __init__(self, json_data):
        self.suggested_edit_id = json_data["suggested_edit_id"]
        if "proposing_user" in json_data:
            self.proposing_user = User(json_data["proposing_user"])
        else:
            self.proposing_user = User(None)
        self.approval_date = -1
        self.rejection_date = -1
        if "approval_date" in json_data:
            self.approval_date = json_data["approval_date"]
        if "rejection_date" in json_data:
            self.rejection_date = json_data["rejection_date"]
