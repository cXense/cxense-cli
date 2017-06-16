#!/bin/bash

cd "$(dirname $0)"
if [[ -n "$(git status --porcelain)" ]]; then
    echo "Git repo is dirty, please commit or discard changes before pushing" 2>&1
    exit 1
fi
# Subtree commands must be run from the toplevel of the working tree.
cd "$(git rev-parse --show-toplevel)"
echo "Pushing subtree cli to cxense-cli on GitHub, this will take some time..."
git subtree --prefix cli push git@github.com:cXense/cxense-cli.git master
