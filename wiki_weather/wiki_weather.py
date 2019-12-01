import requests
import bs4
import pprint
import re
import sys
import getopt

def get_soup_for_city(city):
    res = requests.get('https://en.wikipedia.org/wiki/{}'.format(city))
    res.raise_for_status()

    return bs4.BeautifulSoup(res.text, features='html.parser')

def get_tables(soup):
    tables = soup.select('table')
    return [x for x in tables if len(x.select('a[href="/wiki/Sunshine_duration"]')) > 0]

def get_parsed(tables, city):
    tables_parsed = []

    for table in tables:
        result = {'city': city, 'metadata': [], 'keys': {}}
        trs = table.select('tr')
        for tr in trs:
            ths = tr.select('th')
            if len(ths) == 0:
                continue

            tds = tr.select('td')
            if (len(tds) == 0):
                result['metadata'].append(ths[0].text.replace('\n', ''))
                continue

            result['keys'][ths[0].text.replace('\n', '')] = [str_to_float(x.text) for x in tds]

        tables_parsed.append(result)

    return tables_parsed

def str_to_float(string):
    res = string.replace('\n', '')
    res = res.replace('−', '-')
    res = res.replace(',', '')
    res = re.sub(r'\(.*\)', '', res)
    return float(res)

def main(cities):
    weathers = []

    for city in cities:
        soup = get_soup_for_city(city)
        tables = get_tables(soup)
        parsed_tables = get_parsed(tables, city)

        for x in parsed_tables:
            weathers.append(x)

    return weathers

def get_weather_keys(weathers):
    return set([keys
        for city_table in weathers
        for keys in city_table['keys']
    ])

def get_values_dict(weathers):
    weather_param_keys = get_weather_keys(weathers)
    values_dict = dict([(x, []) for x in weather_param_keys])

    for city_table in weathers:
        for key in city_table['keys']:
            row = []
            row.append(city_table['city'])
            row.append('; '.join(city_table['metadata']))

            for value in city_table['keys'][key]:
                row.append(value)

            values_dict[key].append(row)

    return values_dict

def usage():
    print('python wiki-weather.py Berlin Vienna Moscow')

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], 'h', ['help'])
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()

    weathers = main(args)
    pprint.pprint(weathers)
# cities = ['Vienna', 'Berlin', 'Munich', 'Porto', 'Hamburg', 'Saint_Petersburg', 'Moscow', 'Volgograd', 'Kemerovo']

