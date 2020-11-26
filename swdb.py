"""Module to provide an interface class for the api at swafarm.com"""
import requests

class SummonersWarDB():
    """Class to provide an interface to swafarm.com's api"""
    def __init__(self):
        """Constructor setting api prefixes"""
        self.__url_prefix = 'https://swarfarm.com/api/v2/'
        self.__image_url = 'https://swarfarm.com/static/herders/images/monsters/'

    def query_name(self, name, element=None):
        """Query the api by the monster name and return an id number for it's awakened/unawakened state"""
        url = '{0}monsters'.format(self.__url_prefix)
        payload = {'name': name}
        if element is not None:
            payload['element'] = element
        response = requests.request('get', url, params=payload)
        if response.json()['results']:
            monster = response.json()['results'][0]
            if monster['awakens_from'] is not None:
                return monster['awakens_from']
            return monster['awakens_to']
        return None


    def query_id(self, mon_id):
        """Query by the id_number for an easier match"""
        url = '{0}monsters/{1}/'.format(self.__url_prefix, mon_id)
        response = requests.request('get', url)
        monster = response.json()
        return (monster['name'], monster['element'], monster['image_filename'])

    def who_is(self, name):
        """Method for determining call structure to fetch data from the api"""
        type_id = None
        send_awakened = False
        if ' ' in name:
            element, tmp_name = name.split(' ', maxsplit=1)
            if element.lower() in ['wind', 'fire', 'water', 'light', 'dark']:
                send_awakened = True
                name = tmp_name
                type_id = self.query_name(name, element.lower())
        else:
            type_id = self.query_name(name)
        name, element, image = (self.query_id(type_id))
        if send_awakened:
            monster_info = {'title': '{0}'.format(name),
                            'set_image': '{0}{1}'.format(self.__image_url, image)}
        else:
            monster_info = {'title': '{0} {1}'.format(element, name),
                            'set_image': '{0}{1}'.format(self.__image_url, image)}
        if type_id:
            return monster_info
        return 'I don\'t know what monster that is, maybe check your spelling?'

if __name__ == '__main__':
    sw = SummonersWarDB()
    print(sw.who_is('elsharion'))
    print(sw.who_is('Water Hell Lady'))
    print(sw.who_is('shamann'))
