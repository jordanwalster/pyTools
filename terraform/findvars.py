#!/opt/homebrew/bin/python3
import os

import hrequests
import json

tfToken = os.getenv("TERRAFORM_TOKEN")
orgName = ""  # Set org name to fetch worksapces
wsURL = f"https://app.terraform.io/app/{orgName}/workspaces/"


def getWorkspaces():
    page_number = 1
    tfWorkspaceList = []

    while True:
        params = {'page[number]': page_number}

        response = getAPIEndpoint(2, None, params)

        if response.status_code == 200:
            tfJSON = json.loads(response.content)
            for workspace in tfJSON["data"]:
                tfWorkspaceList.append(workspace['id'])
            if response.json()['links']['next'] is not None:
                page_number += 1
            else:
                break
    return tfWorkspaceList


def createLink(content, ws=None, suffix=None):
    urlSuffix = "#" + suffix if suffix is not None else ""
    return f"\x1b]8;;{wsURL}{ws}/variables{urlSuffix}\x1b\\{content}\x1b]8;;\x1b\\"


def getAPIEndpoint(mode, ws, params=None):
    headers = {
        'Authorization': f'Bearer {os.getenv("TERRAFORM_TOKEN")}',
        'Content-Type': 'application/vnd.api+json'
    }
    tfAPIUrl = f"https://app.terraform.io/api/v2/workspaces/{ws}" if ws else wsURL
    if mode == 1:
        tfAPIUrl += "/vars"

    response = hrequests.get(url=tfAPIUrl, headers=headers, params=params)
    if not ws:
        return response
    return json.loads(response.content)


def getWorkspaceName(tfWorkspaceID):
    data = getAPIEndpoint(0, tfWorkspaceID)
    return data["data"]["attributes"]["name"]


def variableList(wsName, variables):
    newLine = False
    for var in variables:
        if searchQuery != var:
            print(f"└─ {createLink(var[0], wsName, var[1])}")
            newLine = True
    # Print blank line to separate workspaces.
    if newLine:
        print("")


def searchWorkspaces(searchType):
    workspaceJSON = {}
    for tfWorkspaceID in getWorkspaces():
        data = getAPIEndpoint(1, tfWorkspaceID)

        for variable in data["data"]:
            variableName = variable["attributes"]["key"]
            variableValue = variable["attributes"]["value"]
            variableID = variable["id"]
            if searchType == "V":
                search = variableValue
            else:
                search = variableName

            try:
                if searchQuery in search:
                    workspaceName = getWorkspaceName(tfWorkspaceID)
                    if workspaceName in workspaceJSON:
                        workspaceJSON[workspaceName][0]["matches"] += 1
                        workspaceJSON[workspaceName][0]["values"].append([variableName, variableID])
                    else:
                        workspaceJSON[workspaceName] = [{"matches": 1, "values": [[variableName, variableID]]}]
            except TypeError:
                pass

    return workspaceJSON


if __name__ == "__main__":
    searchQuery = input("Search query: ")
    searchType = input("Search for Variable [N]ame or \033[1m[V]\033[0malue: ")
    text = "name" if searchType == "N" else "value"
    print(f"Searching workspaces by variable {text}...\n")
    if searchType == "":
        searchType = "V"

    workspaces = searchWorkspaces(searchType)

    if workspaces:
        for workspace in workspaces:
            matches = workspaces[workspace][0]["matches"]
            values = workspaces[workspace][0]["values"]
            if matches > 1:
                print(f"{matches} matches in " + createLink(workspace, workspace))
            else:
                print(f"{matches} match in " + createLink(workspace, workspace))
            variableList(workspace, values)
    else:
        print("No matches found.")

