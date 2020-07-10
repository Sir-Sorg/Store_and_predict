import mysql.connector
import requests
from bs4 import BeautifulSoup
import re
from sklearn import tree


def checker(new_motorcycle_tuple, old_motorcycle_tuple):
    for index in range(5):
        if new_motorcycle_tuple[index] != old_motorcycle_tuple[index]:
            return False
    return True


def get_property():
    yield name_dic.get(input('Enter Your desired Motorcycle name carefully. Like (وسپا پریماورا 150) : '))
    year = int(input(
        'Enter the year of manufacture of your desired Motorcycle. It doesnt matter if its Shamsy or Milladi (We handle that) : '))
    yield year if year <= 1800 else year - 621
    yield int(input('Enter the performance of your desired Motorcycle : '))
    yield city_dic.get(input('Enter the location of Your desired Motorcycle : '))


page = 1
agreed = 'توافقی'
zero = 'صفر'
while True:
    response = requests.get('https://bama.ir/motorcycle/?page='+str(page))
    soup = BeautifulSoup(response.text, 'html.parser')
    price = soup.find_all('p', class_='cost')
    price = list(
        map(lambda this_tag: this_tag.text.replace('تومان', '').replace(',', '').strip() if len(this_tag.text) <= 20 and this_tag.text.find(agreed) == -1 else 'illegal_value', price))
    name_of_motorcycle = soup.find_all('a', attrs={'itemprop': 'url'})
    name_of_motorcycle = list(
        map(lambda this_tag: this_tag.text.replace('\n', '').replace('،', '').strip(), name_of_motorcycle))
    production_year = soup.find_all(
        'span', class_='price year-label hidden-xs', attrs={'itemprop': 'releaseDate'})
    production_year = list(map(lambda this_tag: ''.join(re.findall(
        r'\d+', this_tag.text)) if int(''.join(re.findall(
            r'\d+', this_tag.text))) <= 1800 else int(''.join(re.findall(
                r'\d+', this_tag.text))) - 621, production_year))
    operation = soup.find_all('p', class_='price hidden-xs')
    operation = list(map(lambda this_tag: this_tag.text.replace(
        'کارکرد', '').replace(',', '').strip() if this_tag.text.find(zero) == -1 else '0', operation))
    location = soup.find_all('p', class_='provice hidden-xs')
    location = list(map(lambda this_tag: re.findall(
        r'\w+', this_tag.text)[0], location))

    all_prop = list()
    for index in range(len(name_of_motorcycle)):
        if price[index] != 'illegal_value':
            all_prop.append((name_of_motorcycle[index], production_year[index],
                             operation[index], location[index], price[index]))
    # Write Property togheder with Order : Name Year Operation City Price
    mydb = mysql.connector.connect(
        host='localhost', user='sorg', password='1234', database='bama_motorcycle')
    mycursor = mydb.cursor()
    # TODO read data from database and compare it with Repetitious
    read_data = 'SELECT * FROM motorcycles'
    mycursor.execute(read_data)
    myresult = mycursor.fetchall()
    base_command = 'INSERT INTO motorcycles VALUES (%s,%s,%s,%s,%s)'
    # If Dont Copy, val be aliasing of all_prop and we have broblem in Index of Removing For
    val = all_prop.copy()
    for this_new_motorcycle in all_prop:
        for this_row in myresult:
            if checker(this_new_motorcycle, this_row):
                val.remove(this_new_motorcycle)
                break
    if len(val) > 0:
        mycursor.executemany(base_command, val)
        mydb.commit()
        print(mycursor.rowcount, "Record was inserted.")
    else:
        print('We dont have new record to insert.')
        break  # If in new page we dont have new Data So definitely we dont have it in oldest page

    if soup.find('div', class_='car-ad-list next'):  # checking to reach to last page
        page += 1
    else:
        break

menu_option = input('''What Will you Do :
1 - Find Motorcycle betwen Favorite price ---> Enter 1
2 - Predict the Price of Favorite Motorcycle ---> Enter 2
Give me : ''')
if menu_option == '1':
    price_range = input(
        'Enter your desired price just separate them with a comma (,). Order is not important : ')
    price_range = price_range.split(',')
    price_range = list(map(lambda this_price_in_string: int(
        this_price_in_string), price_range))
    price_range.sort()
    price_range = tuple(price_range)
    base_command = 'SELECT * FROM motorcycles WHERE price BETWEEN %s AND %s'
    mycursor.execute(base_command, price_range)
    myresult = mycursor.fetchall()
    for name_of_m, year_of_m, operation_of_m, city_of_m, price_of_m in myresult:
        print('Motorcycle %s Model %s With a performance of %s km Located in %s with Priced at $ %s .' % (
            name_of_m, year_of_m, operation_of_m, city_of_m, price_of_m))
        # Write Motorcycle in Order : Name Year Operation City Price
elif menu_option == '2':
    clf = tree.DecisionTreeClassifier()
    X = list()
    Y = list()
    city_dic = dict()
    name_dic = dict()
    city_dic_value = 0
    name_dic_value = 0
    read_data = 'SELECT * FROM motorcycles'
    mycursor.execute(read_data)
    myresult = mycursor.fetchall()
    for this_row in myresult:
        # We keep performances that ecual to '-' for showing in Find Motorcycle (Part 1th of the menu)
        if this_row[2] != '-':
            if not (this_row[3] in city_dic):
                city_dic[this_row[3]] = city_dic_value
                city_dic_value += 1
            if not (this_row[0] in name_dic):
                name_dic[this_row[0]] = name_dic_value
                name_dic_value += 1
            X.append([name_dic.get(this_row[0]), int(this_row[1]),
                      int(this_row[2]), city_dic.get(this_row[3])])
            Y.append([int(this_row[4])])
    target_column = list()
    for this_one in get_property():
        target_column.append(this_one)
    target_column = [target_column]
    clf.fit(X, Y)
    print(clf.predict(target_column))
else:
    print('Undefined Command ! Exiting')
mydb.close()
