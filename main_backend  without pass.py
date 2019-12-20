import requests
import os
import pprint
import xlwt
import pandas as pd
from transliterate import translit


LOGIN = 'xxxxx'
PASS = 'xxxxxx'

url_users = 'http://learningrussia.hikvision.com/api/v1/users/search'
url_user = 'http://learningrussia.hikvision.com/api/v1/users/'
url_courses ='https://yourdomain.learnupon.com/api/v1/courses/'
url_enrollment ='https://yourdomain.learnupon.com/api/v1/enrollments/search'
courses_HCSA = [{'id': '664193', 'name': 'Тестирование Сертификации HCSA версия 8', 'type': 'HCSA'},
                {'id': '664991', 'name': 'Тестирование Сертификации HCSA версия 8', 'type': 'HCSA'}]
courses_HCSA_AAI = [{'name': 'Тестирование HCSA-AAI (non-video)', 'id': '654540', 'type': 'HCSA-AAI'}]
courses_HCSP = [{'name': 'Тестирование Сертификации HCSP', 'id': '554901', 'type': 'HCSP'}]
#меняем следующие строки
courses = courses_HCSP
date_from = '2019-12-01'
date_to = '2019-12-25'


def delete_course(course_id):
    childs = get_childs(course_id)
    if childs:
        for child in childs:
            print('child {} exist. \n Please Check it First'.format(child['id']))
        return childs
    d = requests.delete('{}{}'.format(url_courses, course_id), auth=(LOGIN, PASS))
    print('deleted Responce {}'.format(d))
    return 0


def get_course_id_by_name(name):
    responce = requests.get(url_courses, auth=(LOGIN, PASS), params={'name': name})
    print(responce.json())
    id = responce.json()['courses'][0]['id']
    soutce_id = responce.json()['courses'][0]['source_id']
#    return id, soutce_id
    return id


def get_childs(id):
    responce = requests.get(url_courses, auth=(LOGIN, PASS), params={'source_id': id})
    childs = responce.json()['courses']
    return childs


def get_tests():
    tests =[]
    responce = requests.get(url_courses, auth=(LOGIN, PASS))
    courses = responce.json()['courses']
    for course in courses:
        if 'HCSA' in course['name'] and 'Тестирование' in course['name']:
            tests.append({'name': course['name'], 'id': course['id']})
    return tests


def get_user_by_email(user_email):
    responce = requests.get(url_users, auth=(LOGIN, PASS), params={'email': '{}'.format(user_email)})
    return responce.json()['user']

def get_user_by_id(user_id):
    responce = requests.get('{}{}'.format(url_user,user_id), auth=(LOGIN, PASS))
    return responce.json()['user']


def get_enrollment_by_course_and_date(course, date_from , date_to):
    responce = requests.get(url_enrollment, auth=(LOGIN, PASS),
                            params={'course_id': course['id'],
                                    'date_from': date_from,
                                    'date_to': date_to}).json()
    return responce['enrollments']


def courseReport(enrollments, report =[]):
    #report = []
    for enrollment in enrollments:
        #user = get_user(enrollment['email'])
        user = get_user_by_id(enrollment['user_id'])
        print(user[0]['CustomData'])
        report.append({'Candidate name': '{} {}'.format(enrollment['first_name'], enrollment['last_name']),
                       'user_id': enrollment['user_id'],
                       'email': enrollment['email'],
                       'Customer Company': user[0]['CustomData']['company'],
                       'percentage': enrollment['percentage'],
                       'City': user[0]['CustomData']['city'],
                       'Cert Number': 'xxxx-xxxx-xxxx-xxxx',
                       'Type': courses[0]['type']})
    return report


def coursesReport(courses, date_from, date_to, report=[]):
    for course in courses:
        enrollments = get_enrollment_by_course_and_date(course, date_from, date_to)
        report = courseReport(enrollments, report)
        #print('Report:')
        #pprint.pprint(report)

        if report != []:
            wb = xlwt.Workbook()
            write_exel_report(wb, report)
            wd = os.getcwd()
            if __name__ == '__main__':
                wb.save('{}/{}.xls'.format(wd, course['name']))
            return wb

def write_exel_report(wb, courseReport, transliterate=True):
    ws = wb.add_sheet('Report')
    ws.col(0).width = 256 * 20
    ws.col(2).width = 256 * 40
    ws.col(3).width = 256 * 20
    ws.col(4).width = 256 * 20
    ws.col(5).width = 256 * 20
    ws.col(6).width = 256 * 20
    ws.col(7).width = 256 * 20
    ws.col(8).width = 256 * 20
    print(courseReport[0].keys())
    for (i, header) in enumerate(courseReport[0].keys()):
        ws.write(0, i, header)
        for (j, customer) in enumerate(courseReport):
            if transliterate and not isinstance(customer[header], int) and customer[header] is not None:
                print(customer[header])
                ws.write(j+1, i, translit(customer[header], 'ru', reversed=True))
            else:
                ws.write(j + 1, i, customer[header])
    return 0

def exel_to_lu(wb):
    frame = pd.read_excel(wb)
    print(frame)
    for i, user_id in enumerate(frame['user_id']):
        cert_number = frame.loc[[i], ["Cert Number"]].to_string(header=False, index=False)
        type = frame.loc[[i], ["Type"]].to_string(header=False, index=False)

        print('{{"User": {{"CustomData" : {{"HCSA Cert number":"{}"}} }}}}'.format(cert_number))

        if type == 'HCSA':
            responce = requests.put('http://learningrussia.hikvision.com/api/v1/users/2740401',
                                    data='{{"User": {{"CustomData" : {{"HCSA Cert number":"{}"}} }}}}'.format(cert_number),
                                    auth=(LOGIN, PASS) ,
                                    headers={'Content-Type': 'application/json'})
        if type == 'HCSA-VMS':
            responce = requests.put('http://learningrussia.hikvision.com/api/v1/users/2740401',
                                    data='{{"User": {{"CustomData" : {{"HCSA-VMS":"{}"}} }}}}'.format(cert_number),
                                    auth=(LOGIN, PASS),
                                    headers={'Content-Type': 'application/json'})
        if type == 'HCSP':
            responce = requests.put('http://learningrussia.hikvision.com/api/v1/users/2740401',
                                    data='{{"User": {{"CustomData" : {{"HCSP Cert number":"{}"}} }}}}'.format(cert_number),
                                    auth=(LOGIN, PASS) ,
                                    headers={'Content-Type': 'application/json'})
        if type == 'HCSA-AAI':
            responce = requests.put('http://learningrussia.hikvision.com/api/v1/users/2740401',
                                    data='{{"User": {{"CustomData" : {{"HCSA AAI Cert number":"{}"}} }}}}'.format(cert_number),
                                    auth=(LOGIN, PASS) ,
                                    headers={'Content-Type': 'application/json'})
    return 0


if __name__ == '__main__':
    #exel_to_lu('./Тестирование HCSA-AAI (non-video).xls')


    report = []
    # переменная не обнуляется \ переписать
    coursesReport(courses, date_from, date_to, report)





    # Инфо про курс
    #    responce = requests.get(url_courses, auth=(LOGIN, PASS), params={'name': course['name']})
     #   responce2 = requests.get('{}{}'.format(url_courses, course['id']), auth=(LOGIN, PASS))
     #   print(responce.json()['courses'])
     #   print(course['id'], responce2.json())




    # Удаление курса
    #id = get_course_id_by_name('Тестирование Сертификации HCSA версия 6')
    #print('ID is {}'.format(id))
    #delete_course(id)

    #Нельзя удалить курс, который является чьим то источником и указан в SOURCCE_IS
