"""Generic methods for interacting with Wikibase APIs (including the Wikidata API)"""
import json
import requests

class APIError(Exception):
    """Object for API errors"""

def handle_response(response):
    """Deals with potential errors in the response from calls to the Wikibase API"""
    response.raise_for_status()
    json_response = response.json()
    if 'error' in json_response:
        raise APIError(json.dumps(json_response['error']))
    return json_response

def get_entities(wikibase_api_url, id_list, language_list=None):
    """Retrieves a list of entities from the Wikibase API"""
    params = {
        'action': 'wbgetentities',
        'format': 'json',
        'ids': '|'.join(id_list)
    }
    if language_list:
        params['languages'] = '|'.join(language_list)
    response = requests.get(wikibase_api_url, params=params)
    json_response = handle_response(response)
    return json_response

def get_token(session, wikibase_api_url, token_type):
    """Requests a token from the Wikibase API"""
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
    """Logs in to a Wikibase"""
    params = {
        'action': 'login',
        'lgname': username,
        'lgpassword': password,
        'lgtoken': token
    }
    response = session.post(wikibase_api_url, data=params)
    return response, session

def retrieve_credentials_and_get_token(session, config):
    """
    Retrieves Wikibase API credentials from a dictionary and uses those to log in to the Wikibase
    and request an edit token
    """
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

def copy_entities(session, source_api_url, target_api_url, target_csrf_token, id_list,
language_list, entity_type='property', equiv_property=None):
    """
    Copies labels, descriptions, and aliases for entities from the source Wikibase
    to the target Wikibase
    """
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
        print(f"Created new entity with ID {target_id}")
        entity_mapping.append({'source_id': entity_id, 'target_id': target_id})
    return entity_mapping

def create_new_entity(session, api_url, csrf_token, data, entity_type='property'):
    """Creates a new Wikibase entity (default entity type is property)"""
    params = {
        "action": "wbeditentity",
         "new": entity_type,
         "bot": True,
         "token": csrf_token,
         "format": "json",
         "summary": "Bot edit!",
         "data": data
    }
    try:
        response = session.post(api_url, data=params)
        json_response = handle_response(response)
    except APIError as err:
        print(f"Wikibase API error: {err}")
        return err
    else:
        new_id = json_response['entity']['id']
        print(f"Created new {entity_type} with ID {new_id}")
        return json_response

def create_new_property(session, api_url, csrf_token, data):
    """Creates a new Wikibase property"""
    return create_new_entity(session, api_url, csrf_token, data, 'property')

def create_new_item(session, api_url, csrf_token, data):
    """Creates a new Wikibase item"""
    return create_new_entity(session, api_url, csrf_token, data, 'item')
