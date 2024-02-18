# Импортируем необходимые библиотеки для работы с веб-драйвером и парсингом HTML
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import collections
import re
import logging
import json

# Настройка базового конфига для логирования
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s', encoding='utf-8')

# Запись сообщений разного уровня
logging.debug('Это сообщение уровня DEBUG')
logging.info('Это сообщение уровня INFO')
logging.warning('Это сообщение уровня WARNING')
logging.error('Это сообщение уровня ERROR')
logging.critical('Это сообщение уровня CRITICAL')

REPLACE_IN_STREET = "toate"

"""
КОДЫ ПРИДНЕСТРОВЬЯ
https://expertpmr.ru/?rid=4&pid=37
"""

# Путь к драйверу Chrome, который используется для автоматизации браузера
path_to_chromedriver = "C:/Users/Robotics/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe"
service = Service(executable_path=path_to_chromedriver)
driver = webdriver.Chrome(service=service)
sorted_houses = []

# URL-адреса в разных языковых версиях для последующего скрапинга
source_ro = "https://www.posta.md/ro/map/post_office-"
source_ru = "https://www.posta.md/ru/map/post_office-"
source_en = "https://www.posta.md/en/map/post_office-"


def addresses_nested_dict():
    return defaultdict(addresses_nested_dict)


nested_addresses = addresses_nested_dict()

def street_sort_key(street_name):
    # Преобразование ключа к строке, если он не строка
    street_name_str = str(street_name)
    # Извлечение числовой части из названия улицы
    match = re.search(r'\d+', street_name_str)
    if match:
        return int(match.group()), street_name_str  # Возвращает кортеж (число, название улицы)
    return float('inf'), street_name_str  # Улицы без чисел идут в конец списка

def sort_nested_dict(d):
    sorted_dict = collections.OrderedDict()
    for key in sorted(d.keys(), key=street_sort_key):  # Использование специальной функции ключа для сортировки
        if isinstance(d[key], dict):
            sorted_dict[key] = sort_nested_dict(d[key])
        else:
            sorted_dict[key] = d[key]
    return sorted_dict


# Функция для чтения содержимого страницы
def read_content(url):
    driver.get(url)  # Открываем страницу в браузере
    time.sleep(5)
    press_button()  # Вызываем функцию нажатия на кнопку
    time.sleep(2)  # Ждем 5 секунд для полной загрузки страницы
    html = driver.page_source  # Получаем исходный код страницы
    soup = BeautifulSoup(html, "html.parser")  # Используем BeautifulSoup для парсинга HTML
    return soup


def custom_sort(item):
    # Ищем первое вхождение слеша
    slash_index = item.find('/')
    if slash_index != -1:
        # Извлекаем числовую часть до слеша
        number_part = item[:slash_index]
        # Извлекаем числовую часть после слеша
        slash_number_part = item[slash_index + 1:]
        # Пытаемся преобразовать числовую часть после слеша в число
        try:
            slash_number_part = int(slash_number_part)
        except ValueError:
            # Если не удалось преобразовать в число, присваиваем значение 0
            slash_number_part = 0
    else:
        # Если слеш не найден, присваиваем числовой части и числовой части после слеша значение 0
        number_part = item
        slash_number_part = 0
    # Преобразуем числовные части в числа для корректной сортировки
    number_part = int(number_part)

    # Возвращаем кортеж, состоящий из числовой части и числовой части после слеша
    return (number_part, slash_number_part)


# Функция для нажатия на кнопку на странице
def press_button():
    driver.implicitly_wait(5)  # Устанавливаем неявное ожидание в 5 секунд
    buttons = driver.find_elements(By.CSS_SELECTOR, ".button.button--medium.button--dark")  # Ищем кнопку по селектору
    if len(buttons) > 0:
        for i in range(len(buttons)):
            buttons[i].click()  # Если кнопка найдена, нажимаем на каждую


def extract_numbers(input_string):
    # Удаление пробелов вокруг дефисов для упрощения последующего разделения на диапазоны
    input_string = re.sub(r'\s*-\s*', '-', input_string)

    # Поиск чисел, за которыми следует буква, с возможными пробелами и слешами между ними
    with_letters = re.findall(r'\s*\d+\s*[a-zA-Z]|\s*\d+\s*/s*[a-zA-Z]', input_string)
    # print(f'With letters {with_letters}')

    # Поиск чисел, разделённых слешем, с возможными пробелами вокруг слеша
    with_slash = re.findall(r'\s*\d+\s*/\s*\d+', input_string)
    # print(f'With slash {with_slash}')

    # Объединение найденных чисел с буквами и чисел, разделённых слешем, в один список
    extended_numbers = with_slash + with_letters
    # print(f'Numbers with slash and letters {extended_numbers}')

    # Удаление пробелов из элементов списка extended_numbers
    extended_numbers = [number.replace(' ', '') for number in extended_numbers]
    # Удаление букв и следующих за ними пробелов из исходной строки для упрощения разделения на числовые диапазоны
    input_string = re.sub(r'\d*\s*[a-zA-Z]', '', input_string)
    # Удаление слешей [и возможных пробелов вокруг них] и последующих чисел из исходной строки
    input_string = re.sub(r'\d*\s*/\s*\d*', '', input_string)
    # Разделение обработанной строки на отдельные элементы по запятым и пробелам, предшествующим числам
    splited = re.split(r',\s+|\s+,|\s+(?=\d+)', input_string)
    new_houses_list = []
    even_list = []
    odd_list = []
    print(f'Raw Splited {splited}')
    # Обработка каждого элемента разделённой строки
    for i in range(len(splited)):
        # Если элемент содержит дефис, интерпретировать его как числовой диапазон
        if '-' in splited[i]:
            # Извлечение чисел, формирующих диапазон
            for_range = re.findall(r'\d+', splited[i])
            print(f'Range {for_range}')
            if len(for_range) > 1 and for_range[0].isdigit() and for_range[1].isdigit():
                print(f'Range is More Than 1 {for_range}')
                # Создание списка чисел, входящих в диапазон, включая оба конца
                range_list = list(range(int(for_range[0]), int(for_range[1]) + 1))
                if range_list[0] % 2 == 0:
                    even_list += range_list
                elif range_list[0] % 2!= 0:
                    odd_list += range_list
                # Добавление чисел из диапазона в список домов
                new_houses_list += (even_list+odd_list)
                # Преобразование чисел списка в строки для единообразия с extended_numbers
                new_houses_list = list(map(str, new_houses_list))
            elif len(for_range) > 1 and for_range[0].isdigit() and not for_range[1].isdigit():
                print(f'0 is True {for_range}')
                new_houses_list.append(for_range[0])
            elif len(for_range) > 1 and not for_range[0].isdigit() and for_range[1].isdigit():
                print(f'1 is True {for_range}')
                new_houses_list.append(for_range[1])
            else:
                continue


        else:
            print(f'ОБРАБОТАНО? {splited[i]}')
            # Если элемент не содержит дефис, добавить его в список домов
            new_houses_list.append(splited[i])
    # Объединение всех найденных и сгенерированных номеров домов в один список
    all_houses_list = new_houses_list + extended_numbers
    # Удаление пустых строк через filter
    all_houses_list = list(filter(None, all_houses_list))
    all_houses_list = sorted(all_houses_list, key=custom_sort)
    return all_houses_list


def search_house(street):
    list_of_elements = re.sub(r'\s*,\s*', " ", street).split()
    if any(char.isdigit() for char in list_of_elements[-1]):
        current_houses = list_of_elements[-1]
        street = street.replace(current_houses, "").strip()
        street = re.sub(r'\s*,', '', street)
    else:
        current_houses = []
        # В случае, если номер дома не найден, возвращаем None для номера дома и исходную улицу
    return current_houses, street


# Функция для извлечения и печати определенных тегов HTML со страницы
def retrieve_html_tags(url, postal_index):
    soup = read_content(url)  # Читаем содержимое страницы
    # Ищем и получаем необходимые элементы
    the_same_street_houses = []
    print(postal_index)

    header_2 = soup.find("h2", class_="postal-office__container--title mt-16")
    if header_2:
        municipality_district = header_2.get_text()

        header_3 = soup.find_all("h3", class_="postal-office__container--subtitle mt-16")

        if header_3:
            for item in header_3:
                city_village = item.get_text()
                addresses_box = item.find_next_sibling('ul')
                addresses = addresses_box.find_all("li")

                for i in range(len(addresses) - 1):  # Минус один, чтобы избежать выхода за пределы списка
                    current_address_spans = addresses[i].find_all("span")  # Получаем все элементы span для текущего адреса
                    current_street = current_address_spans[0].get_text().strip() if current_address_spans else ""
                    print(f'Current street {current_street}')

                    if len(current_address_spans) > 1:
                        not_sorted_houses = current_address_spans[1].get_text()
                        if any(char.isdigit() for char in not_sorted_houses):
                            current_houses = sorted(extract_numbers(not_sorted_houses), key=custom_sort)
                            nested_addresses[postal_index][municipality_district][city_village][
                                current_street] = current_houses
                        else:
                            current_houses = [""]

                            nested_addresses[postal_index][municipality_district][city_village][
                                current_street] = current_houses
                    else:
                        current_houses, current_street = search_house(current_street)

                        if current_houses != the_same_street_houses:
                            the_same_street_houses.append(current_houses)
                        current_houses = sorted(the_same_street_houses, key=custom_sort)
                        nested_addresses[postal_index][municipality_district][city_village][current_street] = current_houses


# Функция для извлечения данных со страниц для диапазона почтовых индексов
def retrieve_text_by_postal_index(source, start, stop):
    for postal_index in range(start, stop):
        postal_url = source + str(postal_index)  # Формируем URL
        retrieve_html_tags(postal_url, postal_index)  # Извлекаем и печатаем данные со страницы


# Вызов функции для извлечения данных со страниц на русском языке
retrieve_text_by_postal_index(source_ru, 2001, 2005)

# Предположим, что nested_addresses заполнен данными
sorted_addresses = sort_nested_dict(nested_addresses)

# Вывод отсортированного словаря
print(json.dumps(sorted_addresses, indent=4, ensure_ascii=False))

driver.quit()  # Закрываем браузер после выполнения скрипта
