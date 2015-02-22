import requests
from bs4 import BeautifulSoup
import time
import re

api_key = ""
api_url = "https://api.stackexchange.com/2.2/suggested-edits?order=desc&sort=creation&site=stackoverflow&pagesize=50&filter=!*Km*hwlf.lBeKxAb"
api_quota = 300
delay = 1.5
reviewed_confirmed = []
queue = []
action_needed = None
se_fkey = ""


def get_se_fkey(client):  # use ChatExchange's Client and Browser objects to do this
    global se_fkey
    script_with_fkey = client._br.get_soup("http://stackoverflow.com/", None,
                                           None, False).find_all("script")[3].getText()
    se_fkey = re.compile("\"fkey\":\"([a-fA-F0-9]+)\"").search(script_with_fkey).group(1)


def api_request():
    global api_quota
    url = api_url
    if api_key != "":
        url = url + "&key=" + api_key
    r = requests.get(url)
    j = r.json()
    items = j["items"]
    api_quota = j["quota_remaining"]
    return items


def get_review_data(client, s_id):  # use ChatExchange's Client and Browser objects to do this
    req = requests.get("http://stackoverflow.com/suggested-edits/%s" % (s_id,),
                       allow_redirects=False)
    rev_loc = req.headers['Location']
    rev_id = int(rev_loc.split('/')[3])
    rev_data = client._br.post("http://stackoverflow.com/review/next-task/%s" % (rev_id,),
                               {"taskTypeId": 1, "fkey": se_fkey}, None, False).json()["instructions"]
    return rev_data


def process_items(items):
    global reviewed_confirmed
    for item in items:
        suggested_edit_id = item["suggested_edit_id"]
        if "approval_date" in item and suggested_edit_id not in reviewed_confirmed:
            queue.append(suggested_edit_id)


def empty_queue(client):
    global reviewed_confirmed
    global queue
    if len(queue) == 0:
        return
    queue.reverse()
    for s_id in queue:
        soup = BeautifulSoup(get_review_data(client, s_id))
        result_containers = soup.find_all("div", class_="review-results")
        rejections = 0
        for rc in result_containers:
            vote = rc.find("b").getText().lower().strip()
            if vote == "reject":
                rejections += 1
        if rejections >= 2 and action_needed is not None:
            action_needed("Approved with 2 rejection votes", s_id)
        reviewed_confirmed.insert(0, s_id)
        time.sleep(delay)  # to avoid getting request-throttled
    del queue[:]  # clear the queue


def filter_saved_list():
    global reviewed_confirmed
    if len(reviewed_confirmed) > 150:
        reviewed_confirmed = reviewed_confirmed[:150]
