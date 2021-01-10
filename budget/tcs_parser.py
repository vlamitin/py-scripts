import argparse
import csv
import os
import re
from collections import defaultdict

valid_currencies = ['USD', 'RUB', 'EUR']
categories_mapping_dict = {
    'Еда работа': [],
    'Еда магазы': ['Супермаркеты'],
    'Прочее': ['Гос. сборы', 'Другое', 'Кино', 'Книги', 'Переводы/иб', 'Развлечения', 'Разные товары', 'Финан. услуги'],
    'Еда заказ/кафе': ['Рестораны', 'Фастфуд'],
    'Проезд': ['Транспорт'],
    'Медицина': ['Аптеки'],
    'Одежда': [],
    'Покупки в кв': [],
    'Зубы': [],
    'Химия': ['Красота'],
    'Инет, телефоны': [],
    'Ремонт': [],
    'КУ': [],
    'Кошка': [],
    'Ипотека': [],
    'Инет+тел': [],
    'Машина': [],
    'Квартира': [],
    'Кем. КУ': [],
    'Саморазв': ['Образование'],
    'Отпуск': [],
}


def main():
    arg_parser = argparse.ArgumentParser(
        prog="tcs_parser",
        description="Usage: tcs_parser --file_names source_file.xls"
    )
    arg_parser.add_argument('--file_names', nargs='*', type=str,
                            help='space delimited list of csv file names (in transactions date order)', required=True
                            )
    arg_parser.add_argument('--currency', nargs=1, type=str,
                            help=f'{", ".join(valid_currencies)} are supported', required=True
                            )
    args = arg_parser.parse_args()
    args_dict = vars(args)

    arguments_dict = parse_args(args_dict)
    run_scenario(
        arguments_dict['file_names'],
        arguments_dict['currency'],
    )


def parse_args(args_dict):
    if len(args_dict['file_names']) == 0:
        print(f"tcs_parser: at least one file_name is required")
        quit(0)

    for file_name in args_dict['file_names']:
        if not os.path.isfile(file_name):
            print(f"tcs_parser: not a file '{file_name}'")
            quit(0)

    if args_dict['currency'][0] not in valid_currencies:
        print(f"tcs_parser: not supported currency '{args_dict['currency'][0]}', supported list: {valid_currencies}")
        quit(0)

    return {
        'file_names': args_dict['file_names'],
        'currency': args_dict['currency'][0],
    }


def run_scenario(file_names, currency):
    transactions = []

    for file_name in file_names:
        transactions = [*transactions, *read_transactions(file_name)]

    transactions = [tr for tr in transactions if tr['Статус'] == 'OK']
    tcs_categories_dict = to_tcs_catogories_dict(transactions)
    budget_categories_dict = to_budget_categories_dict(tcs_categories_dict)
    tcs_transactions = to_tcs_transactions(transactions, currency, budget_categories_dict)
    tcs_transactions.reverse()
    tcs_transactions = [{**tr, 'date': re.sub(r'([0-9]{2})\.([0-9]{2})\.([0-9]{4})', r'\3-\2-\1', tr['date'])} for tr in tcs_transactions]
    print(tcs_transactions)


def read_transactions(file_name):
    result = []
    with open(file_name, newline='') as f:
        reader = csv.reader(f, delimiter=';')
        headers = []
        for (i, row) in enumerate(reader):
            if i == 0:
                headers = row
            else:
                result.append(dict(zip(headers, row)))

    return result


def to_tcs_catogories_dict(trs):
    res = defaultdict(list)
    for tr in trs:
        res[tr['Категория']].append(tr['Описание'])
    return dict([(k, list(set(res[k]))) for k in res])


def to_budget_categories_dict(tcs_dict):
    res = defaultdict(list)
    for tcs_key in tcs_dict:
        for budget_key in categories_mapping_dict:
            if tcs_key in categories_mapping_dict[budget_key]:
                res[budget_key] = [*res[budget_key], *tcs_dict[tcs_key]]
    return dict(res)


def to_tcs_transactions(trs, currency, budg_dict):
    return [{'date': tr['Дата операции'][:10], 'sum': -float(tr['Сумма операции'].replace(',', '.')), 'category': category_from_tr(tr, budg_dict), 'comment': tr['Описание']}
            for tr in trs if tr['Валюта операции'] == currency]


def category_from_tr(tr, budg_dict):
    res = ''
    for key in budg_dict:
        if tr['Описание'] in budg_dict[key]:
            res = key
    return res


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"tcs_parser: KeyboardInterrupt, exiting ...")
        quit(0)
