import requests
from requests import RequestException
import json


def foo():
    return 'foo'

class Hinterteil(object):

    def __init__(self, url):
        self.url = url


    def get_by_primary(self, table_name, primary_key):

        '''
            Returns a dict representation of a table row by primary key:
            >>> get_by_primary('event', 1)['id']
            1
            >>> get_by_primary('event', 1)['name']
            u'EventA'
            >>> get_by_primary('event', 1)['start_datetime']
            u'2014-10-11T12:00:00'
        '''
        url = self.url
        
        #key = quote(str(primary_key)
        key = primary_key

        r = requests.get(url + table_name + '/' + key )
        if r.ok:
            return r.json()
        else:
            raise IOError(r.status_code)

    def get_single(self, table_name, value, field_name='primary'):
        
        '''
            Returns a single row of a table by looking for a match of `value` 
            in columns `field_name`. 

            Raises an exception if no or more than one
            results found.

            >>> get_single('third_party', 'thirdPartyA', 'name')['name']
            u'thirdPartyA'

            Also wraps get_by_primary():
            >>> get_single('event', 1)['name']
            u'EventA'
        '''
        url = self.url
        
        if field_name == 'primary':
            return self.get_by_primary(table_name, value)
        
        else:
            query = {field_name: value}
           
            r = requests.get(url + table_name + '/', params=query)
        
            if r.ok:
                result = r.json()

                if hasattr(result, '__len__'):
                    num_results = len(result)
                    if num_results > 1:
                        raise IOError('Got more than one row')
                    elif num_results == 0:
                        raise IOError('Got an empty list')
                    else:
                        return result[0]

                return result
            else:
                raise IOError(r.status_code)



    def insert_dict(self, table_name, payload):
        '''
            Inserts a dict representation of a table row.
            Returns the inserted dict if successful.
            Raises RequestException otherwise.

            >>> tp = insert_dict('third_party', {'name': 'thirdPartyD', 'url': 'http://tpD.com'})
            >>> a = get_single('artist', 1)
            >>> ap = insert_dict('artist_page', {'url': 'http://abc.com', 'artist': a['id']}, 'third_party': tp['id']})
            u'thirdPartyC'
        '''
        url = self.url

        json_payload = json.dumps(payload)
        headers = {'content-type': 'application/json'}
        r = requests.post(url + table_name + '/', data=json_payload, headers=headers)
        
        status = str(r.status_code)
        if r.ok:
            try:
                response_dict = r.json()  
            except:
                raise IOError(status + '\n' +r.url +"\n" + str(json_payload))
        
        else:
            try:
                response_dict = r.json()
                msg = response_dict['message']
                ex_msg = status + '/' + msg
                raise RequestException(ex_msg)
            except:
                raise IOError(status + '\n' +r.url +"\n"+  str(json_payload))
    
        return response_dict


    
