import requests
from bs4 import BeautifulSoup
from http import HTTPStatus
import re
import logging

vendors_url = "http://uo.theabyss.ru/?vendors"


def get_craft(s, pattern):
    str_pos = s.find(pattern)
    if str_pos != -1:
        return s[:str_pos], s[str_pos + len(pattern):]
    else:
        return s, None


def get_amount(s):
    first_word = s.split()[0]
    if first_word.isnumeric():
        return s[len(first_word) + 1:], int(first_word)
    return s, None


def get_charges(s):
    # "magic cloak of the abyss [Greater Heal charges: 10]"
    regex = re.search(r'magic (robe|cloak) of the abyss \[([\w\s]+) charges: (\d+)\]', s)
    if regex:
        return regex.groups()[1] + ' ' + regex.groups()[0], int(regex.groups()[2])

    # "glacial staff. charges: 21"
    regex = re.search(r'(.+) charges: (\d+)', s)
    if regex:
        return regex.groups()[0], int(regex.groups()[1])

    # "dying tub (006f0 color 2 charges)"
    regex = re.search(r'dying tub \((?:(?P<color>[\d\w]+) color )?(?P<charges>[\d]+) charges\)', s)
    if regex:
        return ('dying tub' + ' ' + (regex.group('color') or '')).strip(), int(regex.group('charges'))

    return s, None


def get_durability(s):
    if s != '---' or '/' in s:
        current, maximum = s.split('/')
        if current.isnumeric() and maximum.isnumeric():
            return int(current), int(maximum)
    return None, None


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
                    good_name = str(good_row[0])

                    is_bag = good_name[0] == '*'
                    good_name = good_name.lstrip('* ')
                    good_name, crafted_by = get_craft(good_name, ' crafted by ')
                    good_name, looted_by = get_craft(good_name, ' looted by ')
                    good_name, amount = get_amount(good_name)
                    good_name, charges = get_charges(good_name)

                    price_str = str(good_row[1]).replace(' ', '')
                    price = int(price_str) if price_str.isnumeric() else None

                    durability, max_durability = get_durability(str(good_row[2]))

                    yield {
                        'vendor_id': vendor['vendor_id'],
                        'vendor_name': vendor['vendor_name'],
                        'good_name': good_name.lstrip('* '),
                        'good_price': str(price),
                        'durability': str(durability),
                        'max_durability': str(max_durability),
                        'is_bag': str(is_bag),
                        'crafted_by': crafted_by or '',
                        'looted_by': looted_by or '',
                        'amount': str(amount),
                        'charges': str(charges)
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
