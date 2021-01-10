import argparse
import os
import re
from collections import defaultdict
from xlrd import open_workbook


def main():
    arg_parser = argparse.ArgumentParser(
        prog="bcs_parser",
        description="Usage: bcs_parser --file_names source_file_jan.xls source_file_feb.xls --currency USD"
    )
    arg_parser.add_argument('--file_names', nargs='*', type=str,
                            help='space delimited list of xls file names (in transactions date order)', required=True
                            )
    arg_parser.add_argument('--currency', nargs=1, type=str,
                            help='USD, RUR or EUR is supported', required=True
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
        print(f"bcs_parser: at least one file_name is required")
        quit(0)

    for file_name in args_dict['file_names']:
        if not os.path.isfile(file_name):
            print(f"bcs_parser: not a file '{file_name}'")
            quit(0)

    if args_dict['currency'][0] not in ['USD', 'RUR', 'EUR']:
        print(f"bcs_parser: not supported currency '{args_dict['currency'][0]}'")
        quit(0)

    return {
        'file_names': args_dict['file_names'],
        'currency': args_dict['currency'][0],
    }


def run_scenario(file_names, currency):
    transactions = []

    for file_name in file_names:
        transactions = [*transactions, *read_transactions(file_name)]

    # fill budget_categories_dict
    bcs_categories_dict = to_bcs_catogories_dict(transactions)
    budget_categories_dict = to_budget_categories_dict(bcs_categories_dict)

    expenses = [x for x in transactions if x['Тип операции'] == 'Расходная операция']

    bcs_transactions = to_bcs_transactions(expenses, currency, budget_categories_dict)
    bcs_transactions.reverse()
    print(bcs_transactions)


def to_bcs_transactions(trs, currency, budg_dict):
    return [
        {
            'date': normalize_date(tr['Дата совершения операции']),
            'sum': parse_money(tr['Сумма операции'])['value'],
            'category': category_from_tr(tr, budg_dict),
            'comment': tr['Описание'] or tr['Назначение платежа']
        }
        for tr in trs if parse_money(tr['Сумма операции'])['currency'] == currency
    ]


def category_from_tr(tr, budg_dict):
    res = ''
    for key in budg_dict:
        if tr['Описание'] in budg_dict[key]:
            res = key
    return res


def to_bcs_catogories_dict(trs):
    res = defaultdict(list)
    for tr in trs:
        res[tr['Статья расходов']].append(tr['Описание'])
    return dict([(k, list(set(res[k]))) for k in res])


def to_budget_categories_dict(bcs_dict):
    categories_mapping_dict = {
        'Еда работа': [],
        'Еда магазы': ['Супермаркеты'],
        'Прочее': ['Сервис'],
        'Еда заказ/кафе': ['Фастфуд'],
        'Проезд': ['Такси и Каршеринг', 'Транспорт'],
        'Медицина': ['Аптеки'],
        'Одежда': [],
        'Покупки в кв': ['Электроника и ПО', 'Дом, Ремонт'],
        'Зубы': [],
        'Химия': [],
        'Инет, телефоны': ['Связь, интернет, ТВ'],
        'Ремонт': [],
        'КУ': [],
        'Кошка': ['Животные'],
        'Ипотека': [],
        'Инет+тел': [],
        'Машина': [],
        'Квартира': [],
        'Кем. КУ': [],
        'Саморазв': [],
        'Отпуск': [],
    }

    res = defaultdict(list)
    for bcs_key in bcs_dict:
        for budget_key in categories_mapping_dict:
            if bcs_key in categories_mapping_dict[budget_key]:
                res[budget_key] = [*res[budget_key], *bcs_dict[bcs_key]]
    return dict(res)


def read_transactions(file_name):
    workbook = open_workbook(filename=file_name)
    tss_sheet = workbook.sheet_by_name(workbook.sheet_names()[0])

    headers = [tss_sheet.cell_value(0, x) for x in range(tss_sheet.ncols)]

    result = []
    for i in range(1, tss_sheet.nrows - 1):
        row = [tss_sheet.cell_value(i, x) for x in range(tss_sheet.ncols)]
        result.append(dict(zip(headers, row)))

    return result


# '740,00 RUR (740,00 RUR)' -> {'value': 740.0, 'currency': 'RUR'}
# '8\xa0221,71 RUR' -> {'value': 8021.71, 'currency': 'RUR'}
def parse_money(unformatted_summa):
    fixed_summa = re.sub(r'\(.*\)', '', unformatted_summa)
    fixed_summa = r'{}'.format(fixed_summa).replace('\xa0', '').replace(',', '.')
    return {'value': float(fixed_summa.split(' ')[0]), 'currency': fixed_summa.split(' ')[1]}


# '08.04.2020' -> '2020-04-08'
def normalize_date(date_in_ddmmyyyy_format):
    return re.sub(r'([0-9]{2})\.([0-9]{2})\.([0-9]{4})', r'\3-\2-\1', date_in_ddmmyyyy_format)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"bcs_parser: KeyboardInterrupt, exiting ...")
        quit(0)
