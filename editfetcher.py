import requests
from bs4 import BeautifulSoup
import time
import Queue
import actions
from suggestededit import SuggestedEdit


class EditFetcher:
    def __init__(self):
        self.api_key = ""
        self.api_url = "https://api.stackexchange.com/2.2/suggested-edits" \
                       "?order=desc" \
                       "&sort=creation" \
                       "&site=stackoverflow" \
                       "&pagesize=50" \
                       "&filter=!*Km*ho)yKnkgFPNY"
        self.api_quota = 300
        self.delay = 1.5
        self.reviewed_confirmed = []
        self.queue = []
        self.chat_send = None
        self.running = False
        self.action_queue = Queue.Queue()

    @staticmethod
    def format_edit_notification(msg, s_id):
        return "%s: [%s](http://stackoverflow.com/suggested-edits/%s)" \
               % (msg, s_id, s_id)

    def api_request(self):
        url = self.api_url
        if self.api_key != "":
            url = url + "&key=" + self.api_key
        try:
            r = requests.get(url)
        except requests.ConnectionError:
            self.chat_send("Recovered from ConnectionError during API request")
            return False, []
        j = r.json()
        items = j["items"]
        self.api_quota = j["quota_remaining"]
        return True, items

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
            e = SuggestedEdit(item)
            if e.approval_date != -1 \
                    and e.suggested_edit_id not in self.reviewed_confirmed:
                self.queue.append(e)

    def empty_queue(self, ):
        if len(self.queue) == 0:
            return
        self.queue.reverse()
        for s_edit in self.queue:
            s_id = s_edit.suggested_edit_id
            soup = BeautifulSoup(EditFetcher.get_review_data(s_id))
            result_containers = soup.find_all("div", class_="review-results")
            rejections = 0
            for rc in result_containers:
                vote = rc.find("b").getText().lower().strip()
                if vote == "reject":
                    rejections += 1
            if rejections >= 2 and self.chat_send is not None \
                    and s_edit.proposing_user.user_type == "registered":
                self.chat_send(
                    EditFetcher.format_edit_notification(
                        "Approved with 2 rejection votes", s_id
                    )
                )
            elif rejections >= 1 and self.chat_send is not None \
                    and s_edit.proposing_user.user_type != "registered":
                self.chat_send(
                    EditFetcher.format_edit_notification(
                        "Edit by anonymous user approved "
                        "with 1 (or more) rejection vote(s)", s_id
                    )
                )
            self.reviewed_confirmed.insert(0, s_id)
            time.sleep(self.delay)  # to avoid getting request-throttled
        del self.queue[:]  # clear the queue

    def filter_saved_list(self):
        if len(self.reviewed_confirmed) > 150:
            self.reviewed_confirmed = self.reviewed_confirmed[:150]

    def do_work(self, delay):
        self.running = True
        while self.running:
            success, latest_edits = self.api_request()
            if success:
                self.process_items(latest_edits)
                print("Queue length: %s" % (len(self.queue),))
                self.empty_queue()
                self.filter_saved_list()
                print("API quota: " + str(self.api_quota))
            try:
                action = self.action_queue.get(True, delay)
                if action == actions.EXIT:
                    self.running = False
                elif action == actions.FORCE_CHECK:
                    pass
            except Queue.Empty:
                pass

    def stop(self):
        self.action_queue.put_nowait(actions.EXIT)

    def force_check(self):
        self.action_queue.put_nowait(actions.FORCE_CHECK)