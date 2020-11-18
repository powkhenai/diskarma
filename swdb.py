import json
import requests

class swdb():
    def __init__(self):
        self.__url_prefix = 'https://swarfarm.com/api/v2/'
        self.__image_url = 'https://swarfarm.com/static/herders/images/monsters/'

    def query_name(self, name):
        url = '{0}monsters'.format(self.__url_prefix)
        #print(url)
        payload = {'name': name}
        response = requests.request('get', url, params=payload)
        #print(response)
        #print(response.text)
        if response.json()['results']:
            monster = response.json()['results'][0]
            #print(monster['name'])
            #print(monster['awakens_from'])
            return monster['awakens_from']
        else:
            #print('I can\'t find that name...')
            return None


    def query_id(self, id):
        url = '{0}monsters/{1}/'.format(self.__url_prefix, id)
        response = requests.request('get', url)
        #print(response)
        #print(response.text)
        monster = response.json()
        #print('{element} {name}'.format(element=monster['element'], name=monster['name']))
        return '{element} {name}'.format(element=monster['element'], name=monster['name'])

    def who_is(self, name):
        type_id = self.query_name(name)
        #print(type_id)
        if type_id:
            return self.query_id(type_id)
        return 'I don\'t know what monster that is, maybe check your spelling?'

if __name__ == '__main__':
    sw = swdb()
    print(sw.who_is('elsharion'))
