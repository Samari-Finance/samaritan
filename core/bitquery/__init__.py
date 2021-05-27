import requests

from utils.utils import read_api

api_key = read_api('bitquery_api')


def run_query(query):
    headers = {'X-API-KEY': api_key}
    request = requests.post('https://graphql.bitquery.io/',
                            json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception('Query failed and return code is {}.      {}'.format(request.status_code,
                                                                             query))
