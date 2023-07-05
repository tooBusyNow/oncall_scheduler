import sys
from datetime import datetime
from typing import List

import requests


class OncallAPIClient:
    def __init__(self, app_config: str, shedule_config: str):
        self._app_config = app_config
        self._sheduler_config = shedule_config

        self._csrf_token = None
        self._cookies = None

        self._headers = None

    def get_api_endpoint(self, rest_method: str) -> str:
        """
        Accepts rest_method and returns Oncall API endpoint
        """
        return f"{self._app_config['oncall_api']}{rest_method}"

    def oncall_login(self) -> None:
        """
        Sends POST requests on /login endpoint,
        then saves csrf_token and cookies from the response
        """
        oncall_host, oncall_port = self._app_config["oncall_server"].values()
        username, password = self._app_config["oncall_login_creds"].values()

        re = requests.post(
            f"http://{oncall_host}:{int(oncall_port)}/login", data={"username": username, "password": password}
        )

        if re.status_code != 200:
            print("Login failed. Make sure you've set the correct login credentials in app config")
            sys.exit(3)

        self._csrf_token = re.json()["csrf_token"]
        self._cookies = re.headers.get("Set-cookie")

        self._headers = {"X-CSRF-TOKEN": self._csrf_token, "Cookie": self._cookies}

    def create_team(self, name: str, scheduling_timezone: str, email: str, slack_channel: str) -> None:
        """
        Sends POST requests on /teams endpoint to create a new team;
        ----------
        Take into account that /teams endpoint cannot be called using an API key,
        so before making any requests we should already be logged in.
        """

        if name is None or scheduling_timezone is None:
            print("Team name and timezone are required parameters")
            sys.exit(4)

        teams_api = self.get_api_endpoint("teams")
        json = {
            "name": name,
            "scheduling_timezone": scheduling_timezone,
            "email": email,
            "slack_channel": slack_channel,
        }

        re = requests.post(teams_api, json=json, headers=self._headers)
        if re.status_code == 400:
            print(f"Error during creating team: {name}. Some attributes are invalid")
            sys.exit(5)

    def create_roster(self, team_name: str, roster_name: str) -> None:
        """
        Sends POST requests on /teams/{team_name}/rosters endpoint;
        Creates roster named {roster_name} for team {team_name}
        """
        rosters_api = self.get_api_endpoint(f"teams/{team_name}/rosters")
        re = requests.post(rosters_api, json={"name": roster_name}, headers=self._headers)

        if re.status_code == 400:
            print(f"Error during creating roster for team with name {team_name}")
            sys.exit(6)

    def create_user(self, name: str) -> None:
        """
        Sends POST request on /users endpoint;
        Creates user with {name}
        """
        users_api = self.get_api_endpoint("users")
        requests.post(users_api, json={"name": name}, headers=self._headers)

    def update_user(self, name: str, full_name: str, phone_number: str, email: str) -> None:
        """
        Sends PUT requests on /users endpoint;
        Updates user with {name}
        """
        users_api = self.get_api_endpoint(f"users/{name}")
        json = {
            "contacts": {
                "call": phone_number,
                "sms": phone_number,
                "email": email,
                "slack": name,
            },
            "full_name": full_name,
        }

        re = requests.put(users_api, json=json, headers=self._headers)
        if re.status_code == 400:
            print(f"User with name {name} was not found in DB")
            sys.exit(7)

    def add_user_to_roster(self, team_name: str, roster_name: str, user_name: str) -> None:
        """
        Sends POST requests on /teams/{team_name}/rosters/{roster_name}/users endpoint;
        Adds user with name {user_name} to the roster for this team
        """
        rosters_api = self.get_api_endpoint(f"teams/{team_name}/rosters/{roster_name}/users")

        re = requests.post(rosters_api, json={"name": user_name}, headers=self._headers)
        if re.status_code == 400:
            print("Invalid user name caused an error during addition to roster")
            sys.exit(8)

    def create_event(self, date: str, role: str, user_name: str, team_name: str) -> None:
        """
        Sends POST requests on /events endpoint;
        Creates event with {role} on {date}
        """
        seconds_in_one_day = 86400
        date_list = list(map(int, date.split("/")))

        start = datetime(date_list[2], date_list[1], date_list[0], 0, 0).timestamp()
        end = start + seconds_in_one_day

        events_api = self.get_api_endpoint("events")
        json = {
            "start": start,
            "end": end,
            "user": user_name,
            "team": team_name,
            "role": role,
        }

        re = requests.post(events_api, json=json, headers=self._headers)
        if re.status_code == 400:
            print(f"Something wrong with event on date {date}, make sure it is correct!")
            sys.exit(9)

    def get_events_ids_for_team(self, team_name: str) -> List[int]:
        """
        Sends GET request on /events endpoint;
        Recieves list of events for team {team_name} and returns IDs of these events
        """
        events_api = self.get_api_endpoint(f"events?team={team_name}")
        re = requests.get(events_api, headers=self._headers)

        return list(map(lambda x: x["id"], re.json()))

    def flush_old_schedule_for_team(self, team_name: str) -> None:
        """
        Sends DELETE requests on /events/{id}
        for each ID of event from team with name {team_name}
        """
        ids = self.get_events_ids_for_team(team_name)

        for id_ in ids:
            event_api = self.get_api_endpoint(f"events/{id_}")
            requests.delete(event_api, headers=self._headers)

    def process_schedule(self) -> None:
        """
        This function does the following list of actions:
            1) Logs into Oncall API using creds from app config

            2) Creates teams, rosters and users from schedule config
            (these API calls are idempotent and don't produce any duplicates)

            3) Flushes current events state for each team specified in config
            4) Recreates new schedule based on provided config

        """
        self.oncall_login()

        for team in self._sheduler_config["teams"]:
            team_name = team["name"]

            self.create_team(
                name=team_name,
                scheduling_timezone=team["scheduling_timezone"],
                email=team["email"],
                slack_channel=team["slack_channel"],
            )

            roster_name = team_name + " Roster"
            self.create_roster(team_name=team_name, roster_name=roster_name)
            self.flush_old_schedule_for_team(team_name=team_name)

            for user in team["users"]:
                user_name = user["name"]

                self.create_user(name=user_name)
                self.update_user(
                    name=user_name, full_name=user["full_name"], phone_number=user["phone_number"], email=user["email"]
                )

                self.add_user_to_roster(team_name=team_name, roster_name=roster_name, user_name=user_name)

                for event in user["duty"]:
                    self.create_event(date=event["date"], role=event["role"], user_name=user_name, team_name=team_name)

        print('Schedule was successfully updated')
