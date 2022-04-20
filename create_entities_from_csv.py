"""Create Wikibase entities from a CSV file"""
import configparser
import argparse
import json
import requests
import pandas as pd
import wikibase_methods as wb

def create_entities_from_df(session, api_url, csrf_token, entity_df, lang, entity_type='property'):
    """Creates Wikibase entities from a pandas DataFrame of entity data"""
    assert entity_type in set(['property', 'item'])

    def to_data(row):
        data = {
            'labels': {
                lang: {
                    'language': lang,
                    'value': row['label']
                }
            },
            'descriptions': {
                lang: {
                    'language': lang,
                    'value': row['description']
                }
            }
        }
        if entity_type == 'property':
            data['datatype'] = row['datatype']
        return data

    entity_df['data'] = entity_df.apply(to_data, axis=1)
    entity_df['data'].apply(lambda x: wb.create_new_entity(session, api_url, csrf_token,
        json.dumps(x), entity_type))

def main():
    """
    Reads in CSV file with entity labels and descriptions and uses those to create new entities in
    Wikibase
    """
    config = configparser.ConfigParser()
    config.read('.config')

    parser = argparse.ArgumentParser(description='Create Wikibase entities from CSV')
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

    with requests.Session() as session:
        wikibase_api_url, csrf_token, session = wb.retrieve_credentials_and_get_token(session,
            config)
        create_entities_from_df(session, wikibase_api_url, csrf_token, entities_df,
            args.lang, args.type)

if __name__ == '__main__':
    main()
