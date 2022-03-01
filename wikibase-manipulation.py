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
    print(login_token)
    data, session = login(session, 
                          api_url, 
                          login_token, config['CREDENTIALS']['USERNAME'], 
                          config['CREDENTIALS']['PASSWORD'])
    csrf_token_response, session = get_token(session, api_url, 'csrf')
    csrf_token = csrf_token_response['query']['tokens']['csrftoken']
    print(csrf_token)
    return api_url, csrf_token, session

def copy_properties(session, source_api_url, target_api_url, target_csrf_token, id_list, language_list):
    properties_in = get_entities(source_api_url, id_list, language_list)
    properties_in = properties_in['entities']
    keys_to_extract = ['datatype', 'labels', 'descriptions', 'aliases']
    params = {
        "action": "wbeditentity",
         "new": "property",
         "bot": True,
         "token": target_csrf_token,
         "format": "json",
         "summary": "Bot edit!"
    }
    property_mapping=[]
    for pid in id_list:
        data = {key: properties_in[pid][key] for key in keys_to_extract}
        params['data'] = json.dumps(data)
        response = session.post(target_api_url, data=params)
        json_response = handle_response(response)
        target_pid = json_response['entity']['id']
        print("Created new property with ID {}".format(target_pid))
        property_mapping.append({'source_id': pid, 'target_id': target_pid})
    return property_mapping

def main():
    config = configparser.ConfigParser()
    config.read('.config')
    
    parser = argparse.ArgumentParser(description='Load properties into Wikibase')
    parser.add_argument('id_list_file', 
                        help='Text file with list of properties to copy into Wikibase, one PID per line')
    parser.add_argument('language_list_file', 
                        help='Text file with list of language codes in which to copy terms, one code per line')
    parser.add_argument('output_directory', 
                        help='Directory in which to save ID mapping file')
    
    args = parser.parse_args()
    with open(args.id_list_file) as file:
        id_list = file.readlines()
        id_list = [line.rstrip() for line in id_list]
    
    with open(args.language_list_file) as file:
        language_list = file.readlines()
        language_list = [line.rstrip() for line in language_list]
    
    s = requests.Session()
    wikibase_api_url, csrf_token, s = retrieve_credentials_and_get_token(s, config)
    
    property_map = copy_properties(s, WIKIDATA_API_URL, wikibase_api_url, 
                               csrf_token, id_list, language_list)
    
    output_file = os.path.join(args.output_directory, 'property_id_mapping.json')
    with open(output_file, 'w') as fout:
        json.dump(property_map, fout)

if __name__ == '__main__':
    main()

