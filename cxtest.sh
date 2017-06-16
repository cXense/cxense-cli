#!/bin/bash

# Test script for cx.py.

errors=0
tests_run=0
interpreters="python2 python3"
dir=$(dirname $0)

fail() {
    echo "$*" >&2
    exit 1
}

register_failure() {
    local out
    for out in "$@"; do
        echo "$out" >&2
    done
    echo
    let errors++
}

cxrun() {
    local output
    output=$(eval "$1" 2>&1)
    if [[ $? != 0 ]]; then
        echo "$output"
        return 1
    fi
    local jsonparse
    jsonparse=$(jq . <<<"$output" 2>&1 > /dev/null)
    if [[ $? != 0 ]]; then
        echo "JSON parse failed for $output: $jsonparse"
    fi
}

cxtest() {
    local cmd=$1
    local interpreter
    local output
    for interpreter in $interpreters; do
        output=$(cxrun "${cmd/cx.py/$interpreter $dir/cx.py}")
        [[ $? = 0 ]] || register_failure "$interpreter execution of \"$cmd\" failed" "$output"
    done
    let tests_run++
}

[[ -f ~/.cxrc ]] || fail "Missing ~/.cxrc, please configure before running test"
for interpreter in $interpreters; do
    type -t $interpreter > /dev/null || fail "Cannot find $interpreter in PATH, cannot run tests"
done


cxtest "cx.py /public/date"
cxtest "cx.py /profile/content/fetch?json=%7B%22url%22%3A%22http%3A%2F%2Fwww.example.com%22%7D"
cxtest "cx.py /profile/content/fetch '{\"url\": \"http://www.example.com\"}'"
cxtest "echo '{\"url\": \"http://www.example.com\"}' | cx.py /profile/content/fetch -"
# cx.py should write binary responses unaltered to stdout. The test URL is an arbitrary binary resource that doesn't
# require credentials (in order to be able to retrieve with curl for comparison), using https and cxense.com to avoid
# compromising credentials.
binary_url="https://comcluster.cxense.com/Repo/rep.gif"
cxtest "cmp <(cx.py $binary_url) <(curl -s $binary_url)"

echo "$tests_run tests run, $errors errors"
if [[ $errors -gt 0 ]]; then
    exit 1
fi
