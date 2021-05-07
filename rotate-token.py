#!/usr/bin/env python

import json
import os
from datetime import date, timedelta

import requests


def rotate_gitlab_variable(**arguments):
    api_v4_url = arguments["api_v4_url"]
    header = arguments["header"]
    project_id = arguments["project_id"]
    env_var = arguments["env_var"]
    token = arguments["token"]

    base_url = f"{api_v4_url}/projects/{project_id}/variables"
    variables_url = f"{base_url}/{env_var}"

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


def rotate_gitlab_token(**arguments):
    api_v4_url = arguments["api_v4_url"]
    header = arguments["header"]
    project_id = arguments["project_id"]
    author = arguments["author"]

    base_url = f"{api_v4_url}/projects/{project_id}/access_tokens"
    expires_at = date.today() + timedelta(weeks=+1)

    payload = {
        "name": f"{author}",
        "scopes": ["api"],
        "expires_at": f"{str(expires_at)}",
    }

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
        delete_url = f"{base_url}/{str(token_id)}"
        try:
            r = requests.delete(delete_url, headers=header, verify=False)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SystemExit(e)

    print(f"Create new token [name: '{author}']")
    content_type = {"Content-Type": "application/json"}
    headers = {**header, **content_type}

    try:
        r = requests.post(base_url, headers=headers, verify=False, data=json.dumps(payload))
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)

    return r.json()["token"]


def get_project_id(**arguments):

    api_v4_url = arguments["api_v4_url"]
    header = arguments["header"]
    path_with_namespace = arguments["path_with_namespace"]

    project = os.path.basename(path_with_namespace)

    search_url = f"{api_v4_url}/search/?scope=projects&search={project}"

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
    api_v4_url = "https://gitlab.example.org/api/v4"
    author = "Notes"
    env_var = "GITLAB_TOKEN"

    try:
        header = {"PRIVATE-TOKEN": format(os.environ["GITLAB_TOKEN"])}
    except KeyError:
        print("Please set the 'GITLAB_TOKEN' environment variable")
        exit(1)

    for line in open("./projects.txt"):
        li = line.strip()
        if not li.startswith("#"):
            path_with_namespace = line.rstrip()

            print(f"Processing: '{path_with_namespace}'")
            id = get_project_id(
                api_v4_url=api_v4_url,
                header=header,
                path_with_namespace=path_with_namespace,
            )

            if isinstance(id, (int)):
                token = rotate_gitlab_token(
                    api_v4_url=api_v4_url, header=header, author=author, project_id=id
                )
                rotate_gitlab_variable(
                    api_v4_url=api_v4_url,
                    header=header,
                    env_var=env_var,
                    token=token,
                    project_id=id,
                )
            else:
                print(f"WARNING: '{path_with_namespace}' not found")


if __name__ == "__main__":
    main()
