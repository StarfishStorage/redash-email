import time
from enum import Enum

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class APIError(Exception):
    pass


class JobStatus(Enum):
    PENDING = 1
    STARTED = 2
    SUCCESS = 3
    FAILURE = 4
    CANCELLED = 5


class Redash:
    def __init__(self, redash_url, redash_api_key):
        self.url = redash_url
        self.is_shared = {}
        csrf_token, cookies = self._obtain_csrf_token_and_cookies()
        self.headers = {
            "Authorization": f"Key {redash_api_key}",
            "Accept": "application/json",
            "X-CSRF-Token": csrf_token,
        }
        self._cookies = cookies

    def _obtain_csrf_token_and_cookies(self):
        # token is valid for 6 hours, so we don't have to get it every request
        redash_login_url = self.url.replace("api", "login")
        response = requests.head(redash_login_url, allow_redirects=True, verify=False)
        cookies = response.cookies
        # /login may redirect. In such case, cookies will be set by response from `resp.history`
        # which contains response before redirection occurred.
        if not cookies and response.history:
            cookies = response.history[0].cookies  # try getting cookies from redirection page
        csrf_token = cookies.get("csrf_token")
        return csrf_token, cookies

    def get(self, endpoint, params=None):
        reply = requests.get(
            f"{self.url}/{endpoint}",
            params=params,
            headers=self.headers,
            cookies=self._cookies,
            verify=False,
        )
        if reply.status_code == 400:
            print(reply.text)
        reply.raise_for_status()
        return reply.json()

    def post(self, endpoint, data):
        reply = requests.post(
            f"{self.url}/{endpoint}",
            headers=self.headers,
            cookies=self._cookies,
            json=data,
            verify=False,
        )
        if reply.status_code == 400:
            print(reply.text)
            print(data)
        reply.raise_for_status()
        return reply.json()

    def delete(self, endpoint):
        reply = requests.delete(
            f"{self.url}/{endpoint}",
            headers=self.headers,
            cookies=self._cookies,
            verify=False,
        )
        if reply.status_code == 400:
            print(reply.text)
        reply.raise_for_status()
        return reply.json()

    def dashboard_id(self, name):
        reply = self.get("dashboards", {"page_size": 250})
        for dashboard in reply["results"]:
            if dashboard["name"] == name:
                return (dashboard["id"], dashboard["slug"])
        raise APIError(f"dashboard '{name}' not found")

    def dashboard_widget(self, dashboard_id, name):
        # Return dashboard parameters
        reply = self.get(f"dashboards/{dashboard_id}")
        for widget in reply["widgets"]:
            query = widget["visualization"]["query"]
            if query["name"] == name and query["is_archived"] is False:
                parameters = query["options"]["parameters"]
                param_map = {}
                for param in parameters:
                    param_map[param["name"]] = param["value"]
                return (query["id"], param_map)
        raise APIError(f"query '{name}' not found for dashboard_id {dashboard_id}")

    def initiate_query(self, query_id, query_params):
        # run a redash query, and return query_result_id
        # wait for job to complete if query is not cached
        data = {
            "parameters": query_params,
        }
        reply = self.post(f"queries/{query_id}/results", data)
        if "job" in reply:
            status = reply["job"]["status"]
            job_id = reply["job"]["id"]
            while status in (JobStatus.PENDING, JobStatus.STARTED):
                reply = self.get(f"jobs/{job_id}")
                status = reply["job"]["status"]
                if status in (JobStatus.FAILURE, JobStatus.CANCELLED):
                    print(reply)
                time.sleep(2)
            return reply["job"]["query_result_id"]
        return reply["query_result"]["id"]

    def dashboard_public_url(self, dashboard_id):
        # Return public URL, or share if not already set
        reply = self.get(f"dashboards/{dashboard_id}")
        if "public_url" in reply:
            if dashboard_id not in self.is_shared:
                self.is_shared[dashboard_id] = True
            public_url = reply["public_url"]
        else:
            self.is_shared[dashboard_id] = False
            reply = self.post(f"dashboards/{dashboard_id}/share", {})
            public_url = reply["public_url"]
        return public_url

    def dashboard_reset(self, dashboard_id):
        # Return dashboard share to prior state
        if self.is_shared[dashboard_id] is False:
            self.delete(f"dashboards/{dashboard_id}/share")
