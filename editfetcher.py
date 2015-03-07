import requests
from bs4 import BeautifulSoup
import time


class EditFetcher:
    def __init__(self):
        self.api_key = ""
        self.api_url = "https://api.stackexchange.com/2.2/suggested-edits" \
                       "?order=desc" \
                       "&sort=creation" \
                       "&site=stackoverflow" \
                       "&pagesize=50" \
                       "&filter=!*Km*hwlf.lBeKxAb"
        self.api_quota = 300
        self.delay = 1.5
        self.reviewed_confirmed = []
        self.queue = []
        self.action_needed = None

    def api_request(self):
        url = self.api_url
        if self.api_key != "":
            url = url + "&key=" + self.api_key
        r = requests.get(url)
        j = r.json()
        items = j["items"]
        self.api_quota = j["quota_remaining"]
        return items

    @staticmethod
    def get_review_data(s_id):
        req = requests.get("http://stackoverflow.com/suggested-edits/%s"
                           % (s_id,),
                           allow_redirects=False)
        rev_loc = req.headers['Location']
        rev_id = int(rev_loc.split('/')[3])
        req_params = {"taskTypeId": 1}
        response = requests.post("http://stackoverflow.com/review/next-task/%s"
                                 % (rev_id,),
                                 params=req_params)
        if response.status_code != 200:
            raise Exception("Review data response status code is not 200.")
        rev_data = response.json()["instructions"]
        return rev_data

    def process_items(self, items):
        for item in items:
            suggested_edit_id = item["suggested_edit_id"]
            if "approval_date" in item \
                    and suggested_edit_id not in self.reviewed_confirmed:
                self.queue.append(suggested_edit_id)

    def empty_queue(self, ):
        if len(self.queue) == 0:
            return
        self.queue.reverse()
        for s_id in self.queue:
            soup = BeautifulSoup(EditFetcher.get_review_data(s_id))
            result_containers = soup.find_all("div", class_="review-results")
            rejections = 0
            for rc in result_containers:
                vote = rc.find("b").getText().lower().strip()
                if vote == "reject":
                    rejections += 1
            if rejections >= 2 and self.action_needed is not None:
                self.action_needed("Approved with 2 rejection votes", s_id)
            self.reviewed_confirmed.insert(0, s_id)
            time.sleep(self.delay)  # to avoid getting request-throttled
        del self.queue[:]  # clear the queue

    def filter_saved_list(self):
        if len(self.reviewed_confirmed) > 150:
            self.reviewed_confirmed = self.reviewed_confirmed[:150]
