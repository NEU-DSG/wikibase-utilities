# wikibase-code

Python scripts for working with a custom Wikibase installation

## Set-up steps

- Create a bot on your custom Wikibase ([Vanderbilt Libraries](https://heardlibrary.github.io/digital-scholarship/host/wikidata/bot/) has a good set of instructions for doing this), making sure to keep track of the associate username and password
- Create a file named `.config` in this directory that takes the form
```
[CREDENTIALS]
ENDPOINT_URL=http://my-custom-wikibase.com/w/api.php
USERNAME=wikibase-bot-username
PASSWORD=wikibase-bot-password
```
- Run `pip install -r requirements.txt` (ideally from within a [Python virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/))

## Copy entities from Wikidata to custom Wikibase

[copy_entities.py](copy_entities.py) provides functionality for copying the labels, descriptions, and aliases for a (user-provided) set of items or properties in a (user-provided) set of languages from Wikidata to your custom Wikibase.

Run `python3 copy_entities.py -h` for more information on the arguments to provide. Example input files are included in the [example/](example/) directory.

