import requests
from bs4 import BeautifulSoup
import time

api_key = ""
api_url = "https://api.stackexchange.com/2.2/suggested-edits?order=desc&sort=creation&site=stackoverflow&pagesize=50&filter=!*Km*hwlf.lBeKxAb"
api_quota = 300
delay = 1.5
reviewed_confirmed = []
queue = []
action_needed = None


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


def get_review_data(s_id):
    req = requests.get("http://stackoverflow.com/suggested-edits/%s" % (s_id,),
                       allow_redirects=False)
    rev_loc = req.headers['Location']
    rev_id = int(rev_loc.split('/')[3])
    req_params = {"taskTypeId": 1}
    response = requests.post("http://stackoverflow.com/review/next-task/%s" % (rev_id,),
                             params=req_params)
    if response.status_code != 200:
        raise Exception("API response status code is not 200.")
    rev_data = response.json()["instructions"]
    return rev_data


def process_items(items):
    global reviewed_confirmed
    for item in items:
        suggested_edit_id = item["suggested_edit_id"]
        if "approval_date" in item and suggested_edit_id not in reviewed_confirmed:
            queue.append(suggested_edit_id)


def empty_queue():
    global reviewed_confirmed
    global queue
    if len(queue) == 0:
        return
    queue.reverse()
    for s_id in queue:
        soup = BeautifulSoup(get_review_data(s_id))
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
