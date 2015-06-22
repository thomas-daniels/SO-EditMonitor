import requests
from bs4 import BeautifulSoup
import time
import Queue
import actions
from suggestededit import SuggestedEdit
from checkspam import check_spam
import re
import sys


class EditFetcher:
    def __init__(self):
        self.api_key = ""
        self.api_url = "https://api.stackexchange.com/2.2/suggested-edits" \
                       "?order=desc" \
                       "&sort=creation" \
                       "&site=stackoverflow" \
                       "&pagesize=50" \
                       "&filter=!*Km*ho3zW5usnf9A"
        self.api_quota = 300
        self.delay = 1.5
        self.reviewed_confirmed = []
        self.queue = []
        self.chat_send = None
        self.running = False
        self.action_queue = Queue.Queue()
        self.se_fkey = ""
        self.ce_client = None

    def get_se_fkey(self):  # use ChatExchange's objects to do this
        client = self.ce_client
        script_with_fkey = client._br.get("http://stackoverflow.com/", None,
                                          None, False).text
        self.se_fkey = re.compile("\"fkey\":\"([a-fA-F0-9]+)\"")\
                         .search(script_with_fkey).group(1)

    @staticmethod
    def format_edit_notification(msg, s_id, additional):
        if len(additional) == 0:
            return "%s: [%s](http://stackoverflow.com/suggested-edits/%s)" \
                   % (msg, s_id, s_id)
        else:
            return "%s: [%s](http://stackoverflow.com/suggested-edits/%s) | %s"\
                   % (msg, s_id, s_id, " | ".join(additional))

    def api_request(self):
        url = self.api_url
        if self.api_key != "":
            url = url + "&key=" + self.api_key
        try:
            r = requests.get(url)
        except requests.ConnectionError:
            self.chat_send("Recovered from ConnectionError during API request")
            return False, []
        try:
            j = r.json()
        except ValueError:
            self.chat_send(
                "Recovered from ValueError when parsing JSON response."
            )
            return False, []
        items = j["items"]
        self.api_quota = j["quota_remaining"]
        return True, items

    def get_review_data(self, s_id):
        req = requests.get("http://stackoverflow.com/suggested-edits/%s"
                           % (s_id,),
                           allow_redirects=False)
        rev_loc = req.headers['Location']
        rev_id = int(rev_loc.split('/')[3])
        rev_data = self.ce_client._br.post(
            "http://stackoverflow.com/review/next-task/%s" % (rev_id,),
                               {"taskTypeId": 1, "fkey": self.se_fkey},
            None, False).json()["instructions"]
        return rev_data

    def process_items(self, items):
        for item in items:
            e = SuggestedEdit(item)
            spam_reasons = check_spam(e.summary)
            if e.suggested_edit_id not in self.reviewed_confirmed \
                    and len(spam_reasons) > 0 and e.rejection_date == -1:
                self.chat_send(
                    EditFetcher.format_edit_notification(
                        "Potentially bad edit (%s)" % ", ".join(spam_reasons),
                        e.suggested_edit_id, []
                    )
                )
                self.reviewed_confirmed.insert(0, e.suggested_edit_id)
            if e.approval_date != -1 \
                    and e.suggested_edit_id not in self.reviewed_confirmed:
                self.queue.append(e)

    def empty_queue(self):
        if len(self.queue) == 0:
            return
        self.queue.reverse()
        for s_edit in self.queue:
            s_id = s_edit.suggested_edit_id
            soup = BeautifulSoup(self.get_review_data(s_id))
            result_containers = soup.find_all("div", class_="review-results")
            rejections = 0
            additional = []
            for rc in result_containers:
                vote = rc.find("b").getText().lower().strip()
                is_owner = len(rc.find_all("a", class_="owner")) > 0
                if is_owner:
                    additional.append("Approved by OP")
                if vote == "reject":
                    rejections += 1
                elif vote == "edit":
                    additional.append("Edited by reviewer")
            if rejections >= 2 and self.chat_send is not None \
                    and s_edit.proposing_user.user_type == "registered":
                self.chat_send(
                    EditFetcher.format_edit_notification(
                        "Approved with 2 rejection votes", s_id,
                        additional
                    )
                )
            elif rejections >= 1 and self.chat_send is not None \
                    and s_edit.proposing_user.user_type != "registered":
                self.chat_send(
                    EditFetcher.format_edit_notification(
                        "Edit by anonymous user approved "
                        "with 1 (or more) rejection vote(s)", s_id,
                        additional
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
                sys.stdout.flush()
                self.empty_queue()
                self.filter_saved_list()
                print("API quota: " + str(self.api_quota))
                sys.stdout.flush()
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