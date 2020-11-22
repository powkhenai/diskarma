import json
import requests

class swdb():
    def __init__(self):
        self.__url_prefix = 'https://swarfarm.com/api/v2/'
        self.__image_url = 'https://swarfarm.com/static/herders/images/monsters/'

    def query_name(self, name, element=None):
        url = '{0}monsters'.format(self.__url_prefix)
        payload = {'name': name}
        if (element is not None):
            payload['element'] = element
        response = requests.request('get', url, params=payload)
        if response.json()['results']:
            monster = response.json()['results'][0]
            if monster['awakens_to'] is None:
                return monster['awakens_from']
            else:
                return monster['awakens_to']
        else:
            return None


    def query_id(self, id):
        url = '{0}monsters/{1}/'.format(self.__url_prefix, id)
        response = requests.request('get', url)
        monster = response.json()
        return (monster['name'], monster['element'], monster['image_filename'])

    def who_is(self, name):
        type_id = None
        send_awakened = False
        if (' ' in name):
            element, tmp_name = name.split(' ')
            if (element.lower() in ['wind', 'fire', 'water', 'light', 'dark']):
                send_awakened = True
                name = tmp_name
                type_id = self.query_name(name, element.lower())
        else:
            type_id = self.query_name(name)
        name, element, image = (self.query_id(type_id))
        if send_awakened:
            monster_info = {'title': '{0}'.format(name), 'set_image': '{0}{1}'.format(self.__image_url, image)}
        else:
            monster_info = {'title': '{0} {1}'.format(element, name), 'set_image': '{0}{1}'.format(self.__image_url, image)}
        if type_id:
            return monster_info
        return 'I don\'t know what monster that is, maybe check your spelling?'

if __name__ == '__main__':
    sw = swdb()
    print(sw.who_is('elsharion'))
    print(sw.who_is('Wind Phoenix'))
