#!/bin/bash


function install_packages(){
    # install_packages
    #  -install bash-completion required to use poertry bash-completion
    apt-get update -y && apt-get install -y  bash-completion

    echo 'source /etc/profile' >> ${HOME}/.bashrc
}

function install_poerty(){
    # install_poerty()
    # - installs latest version of poetry
    # - installs command completion for poetry
    pip install poetry pre-commit
    poetry completions bash > /etc/bash_completion.d/poetry
    poetry self add poetry-plugin-up
    poetry self add poetry-plugin-export
}

function configure_git(){
    # this configure_git
    # - sets vscode as default editor for git
    # - sets git username if set in the .env file
    #  - sets git email if set in the .env file
    git config --global core.editor "code -w"

    if [ !  -z "${GIT_USER}" ]
    then
        git config --global user.name "${GIT_USER}"
    fi

    if [ !  -z "${GIT_EMAIL}" ]
    then
        git config --global user.email "${GIT_EMAIL}"
    fi
}

function install_git_bash_prompt(){
    # install_git_bash_prompt
    #  - install git bash prompt
    #  - configure git bash propmpt
    #  - enable git bash prompt
    if [ ! -d "${HOME}/.bash-git-prompt" ]
    then
        git clone https://github.com/magicmonty/bash-git-prompt.git  ${HOME}/.bash-git-prompt --depth=1

        echo 'if [ -f "${HOME}/.bash-git-prompt/gitprompt.sh" ]; then
        GIT_PROMPT_ONLY_IN_REPO=1
        source "$HOME/.bash-git-prompt/gitprompt.sh"
fi' >> ${HOME}/.bashrc

    fi
}

function install_poetry_packages(){
    # install poerty packages
    # - configure poetry to create virtual env with in project so that vscode can find python interpreter
    # - check if project file exist

    poetry config virtualenvs.in-project true


    if [ -f "poetry.lock" ]
    then
        poetry lock
    fi


    if [ -f "pyproject.toml" ]
    then
        poetry up
        poetry install
    fi
}


function set_poerty_login_shell(){
    echo 'source $(poetry env info --path)/bin/activate' >> $HOME/.bashrc
}

function setup_precommit(){
    pre-commit autoupdate
    pre-commit install
}

function init_project(){
    python manage.py makemigrations && python manage.py migrate
}

function main(){
    # main
    #  - execute functions in a given order
    install_packages
    install_poerty
    configure_git
    install_git_bash_prompt
    install_poetry_packages
    setup_precommit
    set_poerty_login_shell
    # init_project
}

# call to main
main
