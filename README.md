# Cxense Command Line Interface

This is the Cxense command line interface to all Cxense APIs, `cx.py`.

See [Installing the cx.py Tool](https://wiki.cxense.com/x/3aLCAQ) for documentation, or run
`cx.py --help`.

## Requirements

The Cxense CLI requires Python (2 or 3).

## Installing

Download [cx.py](cx.py), and save it to a directory in your path.

## Contributing

Bug reports and pull requests are appreciated. For an introduction, please see
[Collaborating with issues and pull requests](https://help.github.com/categories/collaborating-with-issues-and-pull-requests/).

## Internals (for Cxense employees)

The master version of the CLI tools is maintained in the `config` repo, under the `cli` directory.
To make a new release to GitHub, first merge your changes to the `config` repo, then run
`publish-to-github.sh`.
