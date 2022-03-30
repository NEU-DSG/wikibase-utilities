import wikibase_methods as wb
import configparser
import argparse
import os
import json
import requests
import pandas as pd

def create_entities_from_df(session, api_url, csrf_token, df, lang, entity_type='property'):
    assert entity_type in set(['property', 'item'])

    def to_data(x):
        data = {
            'labels': {
                lang: {
                    'language': lang,
                    'value': x['label']
                }
            },
            'descriptions': {
                lang: {
                    'language': lang,
                    'value': x['description']
                }
            }
        }
        if entity_type == 'property':
            data['datatype'] = x['datatype']
        return data

    df['data'] = df.apply(lambda x: to_data(x), axis=1)
    df['data'].apply(lambda x: wb.create_new_entity(session, api_url, csrf_token, json.dumps(x), entity_type))

def main():
    config = configparser.ConfigParser()
    config.read('.config')
    
    parser = argparse.ArgumentParser(description='Create Wikibase properties from CSV')
    parser.add_argument('csv_file', 
                        help=' '.join(['CSV file with entities to create in Wikibase;',
                            'must have columns named label and description;',
                            'if adding properties, must also have a datatype column']))
    parser.add_argument('lang', 
                        help='Language code in which to create labels and descriptions')
    parser.add_argument('type', choices=['property', 'item'],
        help='Type of entities to create in Wikibase')

    
    args = parser.parse_args()
    entities_df = pd.read_csv(args.csv_file)

    with requests.Session() as s:
        wikibase_api_url, csrf_token, s = wb.retrieve_credentials_and_get_token(s, config)
        create_entities_from_df(s, wikibase_api_url, csrf_token, entities_df, args.lang, args.type)

if __name__ == '__main__':
    main()