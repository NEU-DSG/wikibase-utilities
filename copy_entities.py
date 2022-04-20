""" Copy entities from Wikidata into custom Wikibase """
import configparser
import argparse
import os
import json
import requests
import wikibase_methods as wb

WIKIDATA_API_URL = 'https://www.wikidata.org/w/api.php'

def main():
    """
    Read in file with list of Wikidata entitiy IDs and copy labels, descriptions, and aliases of
    those entities from Wikidata into other Wikibase
    """
    config = configparser.ConfigParser()
    config.read('.config')

    parser = argparse.ArgumentParser(description='Copy entities from Wikidata into custom Wikibase')
    parser.add_argument('id_list_file',
                        help='Text file with list of entities to copy into Wikibase,'+
                        ' one ID per line')
    parser.add_argument('language_list_file',
                        help='Text file with list of language codes in which to copy terms,'+
                        ' one code per line')
    parser.add_argument('output_directory',
                        help='Directory in which to save ID mapping file')
    parser.add_argument('type', choices=['property', 'item'],
        help='Type of entities to load into Wikibase')
    parser.add_argument('--equiv_property', type=str, required=False,
        help='PID (in target Wikibase) of property representing \'corresponding Wikidata'+
        ' property\' or \'corresponding Wikidata item\'')

    args = parser.parse_args()
    with open(args.id_list_file, encoding='utf-8') as file:
        id_list = file.readlines()
        id_list = [line.rstrip() for line in id_list]

    with open(args.language_list_file, encoding='utf-8') as file:
        language_list = file.readlines()
        language_list = [line.rstrip() for line in language_list]

    session = requests.Session()
    wikibase_api_url, csrf_token, session = wb.retrieve_credentials_and_get_token(session, config)

    entity_map = wb.copy_entities(session, WIKIDATA_API_URL, wikibase_api_url,
                               csrf_token, id_list, language_list,
                               entity_type=args.type, equiv_property=args.equiv_property)

    output_file = os.path.join(args.output_directory, 'entity_id_mapping.json')
    with open(output_file, 'w', encoding='utf-8') as fout:
        json.dump(entity_map, fout)

if __name__ == '__main__':
    main()
