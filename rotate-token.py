import os
from datetime import date, timedelta

import requests

api_v4_url = "https://gitlab.example.org/api/v4"

# token details
author = "Notes"
expires_at = date.today() + timedelta(weeks=+1)
env_var = "GITLAB_TOKEN"

if "GITLAB_TOKEN" in os.environ:
    header = {"PRIVATE-TOKEN": format(os.environ.get("GITLAB_TOKEN"))}
else:
    print("Please set the 'GITLAB_TOKEN' environment variable")
    exit(1)


def rotate_var(project_id, token):

    # project_id = The ID of the current project. This ID is unique across all projects on the GitLab instance
    # token = Project access token

    base_url = f"{api_v4_url}/projects/{project_id}/variables"
    variables_url = base_url + "/" + env_var

    payload = {
        "key": env_var,
        "value": token,
        "masked": "true",
    }

    try:
        r = requests.get(variables_url, headers=header, verify=False)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if r.status_code == 404:
            # The variable is not present, pass
            pass
        else:
            raise SystemExit(e)

    response = r.json()

    if "key" in response and response["key"] == env_var:
        print(f"Variable [name: '{env_var}'] already exists, update it")
        try:
            r = requests.put(variables_url, headers=header, verify=False, data=payload)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SystemExit(e)
    else:
        print(f"Create new variable [name: '{env_var}']")
        try:
            r = requests.post(base_url, headers=header, verify=False, data=payload)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SystemExit(e)


def rotate_token(project_id):

    # project_id = The ID of the current project. This ID is unique across all projects on the GitLab instance

    base_url = f"{api_v4_url}/projects/{project_id}/access_tokens"

    payload = (
        '{ "name": "'
        + author
        + '", "scopes": ["api"], "expires_at": "'
        + str(expires_at)
        + '" }'
    )

    # get the token id
    try:
        r = requests.get(base_url, headers=header, verify=False)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)

    response = r.json()

    counter = 0
    for index in range(len(response)):
        if (
            "name" in response[index]
            and response[index]["name"] == author
            and response[index]["revoked"] == False
            and response[index]["scopes"] == ["api"]
        ):
            position = counter
            counter += 1

    if counter == 1:
        token_id = response[position]["id"]
    elif counter > 1:
        print("WARNING: There are more than one tokens!")

    if "token_id" in locals() and isinstance(token_id, (int)):
        print(f"Token [name: '{author}', id: '{token_id}'] already exists, delete it")
        try:
            r = requests.delete(
                base_url + "/" + str(token_id), headers=header, verify=False
            )
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SystemExit(e)

    print(f"Create new token [name: '{author}']")
    content_type = {"Content-Type": "application/json"}

    try:
        r = requests.post(
            base_url, headers={**header, **content_type}, verify=False, data=payload
        )
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)

    return r.json()["token"]


def project_id(path_with_namespace):
    project = os.path.basename(path_with_namespace)

    search_url = api_v4_url + "/search/?scope=projects&search=" + project

    try:
        r = requests.get(search_url, headers=header, verify=False)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)

    response = r.json()

    for index in range(len(response)):
        if (
            "path_with_namespace" in response[index]
            and response[index]["path_with_namespace"] == path_with_namespace
        ):
            project_id = response[index]["id"]
            return project_id

    return "Invalid project"


def main():

    for line in open("./projects.txt"):
        li = line.strip()
        if not li.startswith("#"):
            path_with_namespace = line.rstrip()

            print(f"Processing: '{path_with_namespace}'")
            id = project_id(path_with_namespace)

            if isinstance(id, (int)):
                token = rotate_token(id)
                rotate_var(id, token)
            else:
                print(f"WARNING: '{path_with_namespace}' not found")


if __name__ == "__main__":
    main()
