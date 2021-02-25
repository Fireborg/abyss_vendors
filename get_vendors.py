# TODO:выкидваю первую звёздочку - флаг сумки
# TODO:отрезать looted by / crafted by в отдельную ячейку
# TODO:если первый символ число - отрезать количество
# TODO:" charges: N" - доставать количество зарядов
# TODO:разделять поломку и максимальную durability
# TODO:получать цвет и число зарядов для краски "dying tub ("

import requests
from bs4 import BeautifulSoup
from http import HTTPStatus
import logging

vendors_url = "http://uo.theabyss.ru/?vendors"


def get_vendors():
    r = requests.get(vendors_url)
    if r.status_code == HTTPStatus.OK:
        soup = BeautifulSoup(r.content, 'lxml')
        vendors_list = soup.find('select', attrs={'name': 'vendor_id'})
        if vendors_list:
            for v in vendors_list.find_all('option'):
                if v['value'] == '0':
                    continue
                yield {
                    'vendor_id': v['value'],
                    'vendor_name': v.string,
                    'url': vendors_url + '=&name=&vendor_id={}'.format(v['value'])
                }


def get_goods():
    for vendor in get_vendors():
        r = requests.get(vendor['url'])
        if r.status_code == HTTPStatus.OK:
            soup = BeautifulSoup(r.content, 'lxml')
            goods_list = soup.find('table', attrs={'class': 'itemTable center'})
            if goods_list:
                for good in goods_list.find_all('tr'):
                    good_row = [f.string for f in good.find_all('td') if 'vendor_name' not in f.attrs.get('class', [])]
                    if len(good_row) != 3:
                        continue
                    yield {
                        'vendor_id': vendor['vendor_id'],
                        'vendor_name': vendor['vendor_name'],
                        'good_name': str(good_row[0]),
                        'good_price': str(good_row[1]),
                        'good_state': str(good_row[2]),
                    }


def main():
    logging.basicConfig(format='[%(asctime)s] %(message)s', filename=r'./logs/get_vendors.log', level=logging.INFO)
    with open('current_state.csv', 'w') as out_file:
        is_head = True
        for g in get_goods():
            if is_head:
                out_file.write('\t'.join(g.keys()) + '\n')
                is_head = False
            out_file.write('\t'.join(g.values()) + '\n')


if __name__ == "__main__":
    main()
