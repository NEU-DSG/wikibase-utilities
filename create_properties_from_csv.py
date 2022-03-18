import wikibase_methods as wb
import configparser
import argparse
import os
import json
import requests
import pandas as pd

def create_properties_from_df(session, api_url, csrf_token, df, lang):
    assert set(['label', 'description', 'datatype']).issubset(df.columns)

    df['data'] = df.apply(lambda x: {
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
            }, 
        'datatype': x['datatype']
        }, axis=1)
    df['data'].apply(lambda x: wb.create_new_property(session, api_url, csrf_token, json.dumps(x)))

def main():
    config = configparser.ConfigParser()
    config.read('.config')
    
    parser = argparse.ArgumentParser(description='Create Wikibase properties from CSV')
    parser.add_argument('csv_file', 
                        help='CSV file with properties to create in Wikibase; must have columns named label, description, and datatype')
    parser.add_argument('lang', 
                        help='Language code in which to create labels and descriptions')

    
    args = parser.parse_args()
    properties_df = pd.read_csv(args.csv_file)

    with requests.Session() as s:
        wikibase_api_url, csrf_token, s = wb.retrieve_credentials_and_get_token(s, config)
        create_properties_from_df(s, wikibase_api_url, csrf_token, properties_df, args.lang)

if __name__ == '__main__':
    main()