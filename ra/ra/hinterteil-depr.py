import requests
from requests.utils import quote
from requests import RequestException
import json


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
        
        #value = quote(str(value))



        if field_name == 'primary':
            return self.get_by_primary(table_name, value)
        
        else:
            query = {'filters': [{'name': field_name, 'op': '==', 'val': value}], 'single': True}
            params= {'q':  json.dumps(query)}
            
            r = requests.get(url + table_name, params=params)
        
            if r.ok:
                return r.json()
            else:
                raise IOError(r.status_code)


    # def insert_dict_a(self, table_name, payload):
    #     '''
    #         Inserts a dict representation of a table row.
    #         Returns the inserted dict if successful.
    #         Raises RequestException otherwise.

    #         >>> tp = insert_dict('third_party', {'name': 'thirdPartyD', 'url': 'http://tpD.com'})
    #         >>> a = get_single('artist', 1)
    #         >>> ap = insert_dict('artist_page', {'url': 'http://abc.com', 'artist': {'id': a['id']}, 'third_party': {'id': tp['id']}})
    #         u'thirdPartyC'
    #     '''
    #     url = self.url

    #     json_payload = json.dumps(payload)
    #     headers = {'content-type': 'application/json'}
    #     r = requests.post(url + table_name, data=json_payload, headers=headers)
        
    #     try:
    #         response_dict = r.json()    
    #     except:
    #         pass
        
    #     if r.ok:
    #         return response_dict
    #     else:
    #         if response_dict and 'message' in response_dict.keys():
    #             res_str = '/' + response_dict['message']
    #         else:
    #             res_str = ''
    #         raise IOError(str(r.status_code) + res_str) 

    def append_child(self, table_name, item, field_name, child_payload):
        
        '''
        Adds a new item to a child table that has a 1:n relation to table_name.
        Returns the parent item on success. Child payload must reference its
        parent object.
        
        >>> e = get_single('event', 2)
        >>> len(e['performances'])
        0
        >>> a = get_single('artist', 1)
        >>> k = get_single('performance_kind', 'PerformanceKindA')
        >>> perf = {'name': 'perfC', 'artist': a, 'kind': k, 'event': e}
        >>> e = append_child('event', e, 'performances', perf)
        >>> len(e['performances'])
        1
        '''
        url = self.url

        payload = {field_name: {'add': [child_payload]}}
        json_payload = json.dumps(payload)
        headers = {'content-type': 'application/json'}
        request_url = url + table_name + '/' + str(item['id'])
        r = requests.put(request_url, data=json_payload, headers=headers)
        
        if r.ok:
            response_dict = r.json()
            return response_dict
        else:
            raise IOError(r.status_code)


    def insert_dict(self, table_name, payload):
        '''
            Inserts a dict representation of a table row.
            Returns the inserted dict if successful.
            Raises RequestException otherwise.

            >>> tp = insert_dict('third_party', {'name': 'thirdPartyD', 'url': 'http://tpD.com'})
            >>> a = get_single('artist', 1)
            >>> ap = insert_dict('artist_page', {'url': 'http://abc.com', 'artist': {'id': a['id']}, 'third_party': {'id': tp['id']}})
            u'thirdPartyC'
        '''
        url = self.url

        json_payload = json.dumps(payload)
        headers = {'content-type': 'application/json'}
        r = requests.post(url + table_name, data=json_payload, headers=headers)
        
        status = str(r.status_code)
        if r.ok:
            try:
                response_dict = r.json()  
            except:
                raise RequestException(status)
        
        else:
            try:
                response_dict = r.json()
                msg = response_dict['message']
                ex_msg = status + '/' + msg
                raise RequestException(ex_msg)
            except:
                raise RequestException(status)
    
        return response_dict