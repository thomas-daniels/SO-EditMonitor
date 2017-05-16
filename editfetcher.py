import requests
from bs4 import BeautifulSoup
import time
import Queue
import actions
from suggestededit import SuggestedEdit
from checkspam import check_spam
import re
import sendmsg
import rejectionreasons
from collections import Counter


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
        self.chat_send = lambda x: None
        self.chat_send_secondary = lambda x: None
        self.running = False
        self.action_queue = Queue.Queue()
        self.se_fkey = ""
        self.ce_client = None
        self.restricted_mode = None

    def get_se_fkey(self):  # use ChatExchange's objects to do this
        client = self.ce_client
        script_with_fkey = client._br.get("http://stackoverflow.com/", None,
                                          None, False).text
        self.se_fkey = re.compile("\"fkey\":\"([a-fA-F0-9]+)\"")\
                         .search(script_with_fkey).group(1)

    @staticmethod
    def format_edit_notification(msg, s_id, additional, tooltip=""):
        if len(additional) == 0:
            return "%s: [%s](http://stackoverflow.com/suggested-edits/%s%s)" \
                   % (msg, s_id, s_id, ' "' + tooltip + '"' if tooltip != "" and tooltip is not None else "")
        else:
            return "%s: [%s](http://stackoverflow.com/suggested-edits/%s%s) | %s"\
                   % (msg, s_id, s_id, ' "' + tooltip + '"' if tooltip != "" and tooltip is not None else "",
                      " | ".join(additional))

    def api_request(self):
        url = self.api_url
        if self.api_key != "":
            url = url + "&key=" + self.api_key
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.ConnectionError:
            self.log_error("Recovered from ConnectionError during API request")
            return False, []
        except requests.HTTPError, h:
            self.log_error("Recovered from HTTPError during API request: %s"
                           % h.message)
            return False, []
        try:
            j = r.json()
        except ValueError:
            self.log_error(
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
        if 'Location' not in req.headers:
            return None
        rev_loc = req.headers['Location']
        rev_id = int(rev_loc.split('/')[3])
        rev_data = None
        try:
            rev_data = self.ce_client._br.post(
                "http://stackoverflow.com/review/next-task/%s" % (rev_id,),
                {"taskTypeId": 1, "fkey": self.se_fkey},
                None, False).json()["instructions"]
        except requests.HTTPError, h:
            self.log_error("Recovered from HTTPError while fetching review task: %s"
                           % h.message)
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
            if e.suggested_edit_id not in self.reviewed_confirmed and e.rejection_date == -1:
                self.queue.append(e)

    def empty_queue(self):
        if len(self.queue) == 0:
            return
        self.queue.reverse()
        processed = 0
        length = len(self.queue)
        for s_edit in self.queue:
            s_id = s_edit.suggested_edit_id
            rev_data = self.get_review_data(s_id)
            if rev_data is None:
                continue
            soup = BeautifulSoup(rev_data)
            result_containers = soup.find_all("div", class_="review-results")
            rejections = 0
            approvals = 0
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
                elif vote == "approve":
                    approvals += 1
            rejection_reasons_soup = soup.find_all("div", class_="rejection-reason")
            rejection_reasons_comply_to_mode = False
            reason_types = []
            for rrs in rejection_reasons_soup:
                reason = rrs.getText().strip()
                reason_types.append(rejectionreasons.get_reason_type(reason))
                if self.restricted_mode.should_report(reason):
                    rejection_reasons_comply_to_mode = True
            if rejections >= 1 and self.chat_send is not None \
                    and rejection_reasons_comply_to_mode \
                    and (s_edit.approval_date != -1 or approvals >= 1):
                count = Counter(reason_types)
                tooltip = "rejection votes: "
                for k in count:
                    tooltip += "{} x {}, ".format(count[k], k)
                tooltip = tooltip.rstrip().rstrip(',')
                self.chat_send_secondary(
                    EditFetcher.format_edit_notification(
                        "{} 1 rejection vote (mode: {})".format(
                            "Approved with" if s_edit.approval_date != -1 else "In the queue with 1 approval vote and",
                            self.restricted_mode.mode
                        ),
                        s_id,
                        additional,
                        tooltip
                    )
                )
                self.reviewed_confirmed.insert(0, s_id)
            if s_edit.approval_date != -1 and s_id not in self.reviewed_confirmed:
                self.reviewed_confirmed.insert(0, s_id)
            processed += 1
            sendmsg.send_to_console_and_ws(
                "Queue length: " + str(length - processed), True
            )
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
                sendmsg.send_to_console_and_ws(
                    "API quota: " + str(self.api_quota)
                )
                sendmsg.send_to_console_and_ws(
                    "Queue length: %s" % (len(self.queue),)
                )
                self.empty_queue()
                self.filter_saved_list()
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

    def log_error(self, msg):
        with open("errorLogs.txt", "a") as f:
            f.write("\nError from editfetcher.py: " + msg + "\n")