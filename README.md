# Rotate Gitlab project access tokens

<!-- vim-markdown-toc GFM -->

* [Secrets rotation as a practice](#secrets-rotation-as-a-practice)
* [Why do even need these tokens in the first place?](#why-do-even-need-these-tokens-in-the-first-place)
* [How do we rotate the tokens?](#how-do-we-rotate-the-tokens)
* [The script](#the-script)
    * [Install the Dependencies](#install-the-dependencies)
    * [Configuration](#configuration)
    * [How do I run this script?](#how-do-i-run-this-script)

<!-- vim-markdown-toc -->

## Secrets rotation as a practice

Secrets are a form of distilled trust. They may be API keys, passwords,
certificates, and other forms of key material.

Traditionally, secrets rotation is performed on a few occasions:

- **A regular policy**: keys should not live forever. Expiring keys and
  rotating them keeps a healthy security posture
- **System upgrade and security hardening**: sometimes a change in the
  authentication infrastructure-moving to better or create faster protocols and
  algorithms requires rotating keys
- **Key leaks, data breaches, and suspected leaks**: in any of these
  unfortunate events, you want to be rotating your keys. Even if you suspect a
  leak has happened, it's still a good practice to just go ahead and rotate

## Why do even need these tokens in the first place?

We have pipelines which need access API access to Gitlab. One case in point
example would be a pipeline which posts the terraform execution plan as a
comment to the merge request.

The pipeline to access the [project access token], hence the token value needs
to be added as a [CI/CD enviroment variable].

## How do we rotate the tokens?

Once generated, the Gitlab tokens can not be changed and basically we need to
delete it and then recreate it. The CI/CD enviroment variable will be updated
with the new generated token.

## The script

### Install the Dependencies

This script is written in Python and it's dependencies can be installed using
[pipenv](https://pipenv.readthedocs.io/en/latest/). Follow the instructions in
[pipenv docs](https://pipenv.readthedocs.io/en/latest/#install-pipenv-today) to
install it.

Once you have pipenv installed you can install all the required python libs by
running:

```bash
pipenv install
```

If you have already installed the libs and want to ensure you are running the
correct versions just run:

```bash
pipenv sync
```

Once you have installed everything you will need to activate the Virtual
Environment that Pipenv created for you before running the script:

```bash
pipenv shell
```

### Configuration

The script does **not** rotate the project access tokens for all the projects
hosted by the Gitlab instance, only the projects provided in the `projects.txt`
file. When adding the projects to `projects.txt`, the project namespace with
the project name must be included.

```
# Lines starting with `#` will be ignored
#acme/repo1
acme/repo2
```

All the tokens created by the script expire in a month and will be
exposed to the jobs via the `GITLAB_TOKEN` CI/CD enviroment variable.

### How do I run this script?

Well, normally you don't. This script is supposed to be executed on a schedule
by Gitlab. If you still need to manually execute, you will need a to create a
[personal access token] and create an enviroment variable and the export it to
all child processes created from that shell.

```bash
export GITLAB_TOKEN="..."
# Run via pipenv
pipenv run ./rotate-token.py
# or activate the virtual environment and run the script directly
pipenv shell
./rotate-token.py
```

> :warning: :warning: :warning: Do **NOT** forget to revoke the token when
> you're done. :warning: :warning: :warning:

[project access token]: https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html
[ci/cd enviroment variable]: https://docs.gitlab.com/ee/ci/variables/
[personal access token]: https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html
