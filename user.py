class User:
    def __init__(self, json_data):
        if json_data is not None:
            self.user_type = json_data["user_type"]
        else:
            self.user_type = "anonymous"