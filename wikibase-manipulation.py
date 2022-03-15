import json
import requests
import configparser
import argparse
import os

WIKIDATA_API_URL = 'https://www.wikidata.org/w/api.php'

class APIError(Exception):
    pass

def handle_response(response):
    response.raise_for_status()
    json_response = response.json()
    if 'error' in json_response:
        raise APIError(json.dumps(json_response['error']))
    return json_response

def get_entities(wikibase_api_url, id_list, language_list=[]):
    params = {
        'action': 'wbgetentities',
        'format': 'json',
        'ids': '|'.join(id_list)
    }
    if len(language_list) > 0:
        params['languages'] = '|'.join(language_list)
    response = requests.get(wikibase_api_url, params=params)
    json_response = handle_response(response)
    return json_response

def get_token(session, wikibase_api_url, token_type):
    params = {
        'action': 'query', 
        'meta': 'tokens', 
        'type': token_type, 
        'format': 'json'
    }
    response = session.get(wikibase_api_url, params=params)
    json_response = handle_response(response)
    return json_response, session

def login(session, wikibase_api_url, token, username, password):
    params = {
        'action': 'login',
        'lgname': username,
        'lgpassword': password,
        'lgtoken': token
    }
    response = session.post(wikibase_api_url, data=params)
    return response, session

def retrieve_credentials_and_get_token(session, config):
    api_url = config['CREDENTIALS']['ENDPOINT_URL']
    login_token_response, session = get_token(session, api_url, 'login')
    login_token = login_token_response['query']['tokens']['logintoken']
    data, session = login(session, 
                          api_url, 
                          login_token, config['CREDENTIALS']['USERNAME'], 
                          config['CREDENTIALS']['PASSWORD'])
    csrf_token_response, session = get_token(session, api_url, 'csrf')
    csrf_token = csrf_token_response['query']['tokens']['csrftoken']
    return api_url, csrf_token, session

def copy_entities(session, source_api_url, target_api_url, target_csrf_token, id_list, language_list, entity_type='property', equiv_property=None):
    entities_in = get_entities(source_api_url, id_list, language_list)
    entities_in = entities_in['entities']
    keys_to_extract = ['labels', 'descriptions', 'aliases']
    if entity_type == 'property':
        keys_to_extract.append('datatype')

    params = {
        "action": "wbeditentity",
         "new": entity_type,
         "bot": True,
         "token": target_csrf_token,
         "format": "json",
         "summary": "Bot edit!"
    }
    entity_mapping=[]
    for entity_id in id_list:
        data = {key: entities_in[entity_id][key] for key in keys_to_extract}
        if equiv_property:
            # Create claim linking this to equivalent property ID in Wikidata
            data['claims'] = [{
                'mainsnak': {
                    'snaktype': 'value',
                    'property': equiv_property,
                    'datavalue': {
                        'value': entity_id,
                        'type': 'string'
                    }
                },
                'type': 'statement',
                'rank': 'normal'
            }]
        params['data'] = json.dumps(data)
        response = session.post(target_api_url, data=params)
        json_response = handle_response(response)
        target_id = json_response['entity']['id']
        print("Created new entity with ID {}".format(target_id))
        entity_mapping.append({'source_id': entity_id, 'target_id': target_id})
    return entity_mapping

def main():
    config = configparser.ConfigParser()
    config.read('.config')
    
    parser = argparse.ArgumentParser(description='Load entities into Wikibase')
    parser.add_argument('id_list_file', 
                        help='Text file with list of entities to copy into Wikibase, one ID per line')
    parser.add_argument('language_list_file', 
                        help='Text file with list of language codes in which to copy terms, one code per line')
    parser.add_argument('output_directory', 
                        help='Directory in which to save ID mapping file')
    parser.add_argument('type', choices=['property', 'item'],
        help='Type of entities to load into Wikibase')
    parser.add_argument('--equiv_property', type=str, required=False,
        help='PID (in target Wikibase) of property representing \'corresponding Wikidata property\' or \'corresponding Wikidata item\'')
    
    args = parser.parse_args()
    with open(args.id_list_file) as file:
        id_list = file.readlines()
        id_list = [line.rstrip() for line in id_list]
    
    with open(args.language_list_file) as file:
        language_list = file.readlines()
        language_list = [line.rstrip() for line in language_list]
    
    s = requests.Session()
    wikibase_api_url, csrf_token, s = retrieve_credentials_and_get_token(s, config)
    
    entity_map = copy_entities(s, WIKIDATA_API_URL, wikibase_api_url, 
                               csrf_token, id_list, language_list, 
                               entity_type=args.type, equiv_property=args.equiv_property)
    
    output_file = os.path.join(args.output_directory, 'entity_id_mapping.json')
    with open(output_file, 'w') as fout:
        json.dump(entity_map, fout)

if __name__ == '__main__':
    main()

