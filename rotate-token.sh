#!/bin/bash

set -euo pipefail

API_V4_URL="https://gitlab.example.org/api/v4"
AUTHOR="Notes"
EXPIRES_AT=$(date -I -d '+1 month')
DATA='{ "name":'\"${AUTHOR}\"', "scopes": ["api"], "expires_at":'\"${EXPIRES_AT}\"' }'
ENV_VAR="GITLAB_TOKEN"

create_var() {
    control=$(curl \
        --request GET \
        --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
        --silent \
        "${API_V4_URL}/projects/$1/variables/${ENV_VAR}" | jq -r '. | select (.key=='\"${ENV_VAR}\"') | .key')

    if [ "$control" == "$ENV_VAR" ]; then
        echo "Variable [name: '${ENV_VAR}'] already exists, update it"
        curl \
            --request PUT \
            --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
            --silent \
            --output /dev/null \
            "${API_V4_URL}/projects/$1/variables/${ENV_VAR}" --form "value=$2" --form "masked=true"
    else
        echo "Create new variable [name: '${ENV_VAR}']"
        curl \
            --request POST \
            --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
            --silent \
            --output /dev/null \
            "${API_V4_URL}/projects/$1/variables" --form "key=${ENV_VAR}" --form "value=$2" --form "masked=true"
    fi

}

create_token() {
    local token_id

    # get the token id
    token_id=$(
        curl \
            --request GET \
            --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
            --silent \
            "${API_V4_URL}/projects/${project_id}/access_tokens" | jq -r '.[] | select (.name=='\"${AUTHOR}\"' and .revoked==false and .scopes[]=="api") | .id'
    )

    if [ -n "$token_id" ]; then
        echo "Token [name: '${AUTHOR}',id: '${token_id}'] already exists, delete it"
        curl \
            --request DELETE \
            --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
            --silent \
            "${API_V4_URL}/projects/$1/access_tokens/${token_id}"
    fi

    echo "Create new token [name: '${AUTHOR}']"
    new_token=$(curl \
        --request POST \
        --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
        --header "Content-Type:application/json" \
        --silent \
        --data "${DATA}" \
        "${API_V4_URL}/projects/$1/access_tokens" | jq -r '.token')
}

main() {
    grep '^[^#]' projects.txt | while read -r project; do
        echo "Processing: '${project}'"
        project_name=$(basename "${project}")
        #project_path=$(dirname "${project}")

        # get the project id
        # shellcheck disable=2086
        project_id=$(
            curl \
                --request GET \
                --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
                --silent \
                "${API_V4_URL}/search/?scope=projects&search=${project_name}" | jq -r '.[] | select (.path_with_namespace=='\"${project}\"') | .id'
        )

        # create/update a new token
        create_token "${project_id}"
        create_var "${project_id}" "${new_token}"
    done
}

main "$@"
