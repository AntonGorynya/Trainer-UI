import requests
import os
import pprint
import xlwt
import pandas as pd
from transliterate import translit, get_available_language_codes
from transliterate.base import TranslitLanguagePack, registry
from docxtpl import DocxTemplate, InlineImage
# for height and width you have to use millimeters (Mm), inches or points(Pt) class :
from docx.shared import Mm, Inches, Pt
import win32com.client as client
import smtplib, ssl, getpass
import time
import logging

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

VERBOSITY_TO_LOGGING_LEVELS = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}


LOGIN = ''
PASS = ''

SNMP_HOST = 'mailru.hikvision.com'
SUBJECT = "HCSA"
FROM = "anton.gorynia@hikvision.com"
#FROM = input("Type your e-mail and press enter:")
PASSWORD_EMAIL = 'Secret'


url_users = 'http://learningrussia.hikvision.com/api/v1/users/search'
url_user = 'http://learningrussia.hikvision.com/api/v1/users/'
url_courses ='https://yourdomain.learnupon.com/api/v1/courses/'
url_enrollment ='https://yourdomain.learnupon.com/api/v1/enrollments/search'
courses_HCSA = [{'id': '750794', 'name': 'Тестирование Сертификации HCSA версия 8', 'type': 'HCSA'},
                {'id': '750758', 'name': 'Тестирование Сертификации HCSA версия 8', 'type': 'HCSA'}]
courses_HCSA_AAI = [{'name': 'Тестирование HCSA-AAI (non-video)', 'id': '654540', 'type': 'HCSA-AAI'}]
courses_HCSP = [{'name': 'Тестирование Сертификации HCSP', 'id': '554901', 'type': 'HCSP'}]
courses_HiWatch = [{'id': '798063', 'name': 'Основной курс HiWatch Academy', 'type': 'HiWatch'}]
WORD_TEMPLATE = 'HCSA Template.docx'
WORD_TEMPLATE_HIWATCH = 'HiWatchTemplate.docx'
#меняем следующие строки
courses = courses_HiWatch
date_from = '2020-01-05'
date_to = '2020-05-06'
logging.basicConfig(level=2)

class ExampleLanguagePack(TranslitLanguagePack):
    language_code = "ru2"
    language_name = "Russian2"
    mapping = (
        u"abvgdeziyklmnoprstufhcC'y'ABVGDEZIYKLMNOPRSTUFH'Y'",
        u"абвгдезийклмнопрстуфхцЦъыьАБВГДЕЗИЙКЛМНОПРСТУФХЪЫЬ",
    )

    reversed_specific_mapping = (
        u"йёэЁЭъьЪЬ",
        u"yeeEE''''"
    )

    pre_processor_mapping = {
        u"zh": u"ж",
        u"ts": u"ц",
        u"ch": u"ч",
        u"sh": u"ш",
        u"sch": u"щ",
        u"yu": u"ю",
        u"ya": u"я",
        u"Zh": u"Ж",
        u"Ts": u"Ц",
        u"Ch": u"Ч",
        u"Sh": u"Ш",
        u"Sch": u"Щ",
        u"Yu": u"Ю",
        u"Ya": u"Я"
    }

registry.register(ExampleLanguagePack)

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
                                    'date_completed': date_to}).json()
                                    #'date_to': date_to}).json()
    logging.debug('enrollments: \n {}'.format(responce))
    return responce['enrollments']

def courseReport(enrollments, report =[]):
    #report = []
    for enrollment in enrollments:
        #user = get_user(enrollment['email'])
        user = get_user_by_id(enrollment['user_id'])
        logging.debug('extract user {} information'.format(enrollment['user_id']))
        print(user[0]['CustomData'])
        report.append({'Candidate name': '{} {}'.format(enrollment['first_name'], enrollment['last_name']),
                       'user_id': enrollment['user_id'],
                       'email': enrollment['email'],
                       'Customer Company': user[0]['CustomData']['company'],
                       'percentage': enrollment['percentage'],
                       'City': user[0]['CustomData']['city'],
                       #'Cert Number': user[0]['CustomData'][choose_cert_type_var_name(courses[0]['type'])],
                       'Type': courses[0]['type'],
                       'Valid': enrollment['cert_expires_at']})
        try:
            report[-1]['Cert Number'] = user[0]['CustomData'][choose_cert_type_var_name(courses[0]['type'])]
        except KeyError:
            if report[-1]['percentage'] != None and report[-1]['percentage'] > 79 and report[-1]['Type'] == 'HiWatch':
                report[-1]['Cert Number'] = report[-1]['user_id']
            else:
                report[-1]['Cert Number'] = None
            print("Проверь значение переменной номера сертификата и типа сертификации")
    logging.debug('courseReport Report: \n {}'.format(report))
    return report

def choose_cert_type_var_name(type):
    if type == 'HCSA':
        return "hcsa_cert_number"
    if type == 'HCSA-AAI':
        return "hcsa_aai_cert_number"
    if type == 'HCSA-VMS':
        return "hcsa-vms"
    if type == 'HCSP':
        return "hcsp_cert_number"
    if type =='HiWatch':
        return "hiwatch_cert_number"


def coursesReport(courses, date_from, date_to, report=[], transliterate=True):
    for course in courses:
        enrollments = get_enrollment_by_course_and_date(course, date_from, date_to)
        report = courseReport(enrollments, report)
        logging.debug('Report: \n {}'.format(report))

        if report != []:
            wb = xlwt.Workbook()
            write_exel_report(wb, report, transliterate=transliterate)
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
            logging.debug('==='*8)
            logging.debug(customer)
            if transliterate and not isinstance(customer[header], int) and customer[header] is not None:
                print(customer[header])
                ws.write(j+1, i, translit(customer[header], 'ru2', reversed=True))
            else:
                ws.write(j + 1, i, customer[header])
    return 0

def exel_to_lu(wb):
    frame = pd.read_excel(wb)
    print(frame)
    for i, user_id in enumerate(frame['user_id']):
        cert_number = frame.loc[[i], ["Cert Number"]].to_string(header=False, index=False)
        cert_number = cert_number.strip()
        type = frame.loc[[i], ["Type"]].to_string(header=False, index=False)
        type = type.strip()
        candidate_name = frame.loc[[i], ["Candidate name"]].to_string(header=False, index=False)
        candidate_name=candidate_name.strip()
        email = frame.loc[[i], ["email"]].to_string(header=False, index=False)
        email=email.strip()

        print(candidate_name)

        print('{{"User": {{"CustomData" : {{"Cert number":"{}"}} }}}}'.format(cert_number))

        if type == 'HCSA':
            responce = requests.put('http://learningrussia.hikvision.com/api/v1/users/{}'.format(user_id),
                                    data='{{"User": {{"CustomData" : {{"HCSA Cert number":"{}"}} }}}}'.format(cert_number),
                                    auth=(LOGIN, PASS) ,
                                    headers={'Content-Type': 'application/json'})
        if type == 'HCSA-VMS':
            responce = requests.put('http://learningrussia.hikvision.com/api/v1/users/{}'.format(user_id),
                                    data='{{"User": {{"CustomData" : {{"HCSA-VMS":"{}"}} }}}}'.format(cert_number),
                                    auth=(LOGIN, PASS),
                                    headers={'Content-Type': 'application/json'})
        if type == 'HCSP':
            responce = requests.put('http://learningrussia.hikvision.com/api/v1/users/{}'.format(user_id),
                                    data='{{"User": {{"CustomData" : {{"HCSP Cert number":"{}"}} }}}}'.format(cert_number),
                                    auth=(LOGIN, PASS) ,
                                    headers={'Content-Type': 'application/json'})
        if type == 'HCSA-AAI':
            logging.debug('{{"User": {{"CustomData" : {{"HCSA AAI Cert number":"{}"}} }}}}'.format(cert_number))
            responce = requests.put('http://learningrussia.hikvision.com/api/v1/users/{}'.format(user_id),
                                    data='{{"User": {{"CustomData" : {{"HCSA AAI Cert number":"{}"}} }}}}'.format(cert_number),
                                    auth=(LOGIN, PASS) ,
                                    headers={'Content-Type': 'application/json'})
        if type == 'HiWatch':
            logging.debug('{{"User": {{"CustomData" : {{"HiWatch Cert Number":"{}"}} }}}}'.format(cert_number))
            responce = requests.put('http://learningrussia.hikvision.com/api/v1/users/{}'.format(user_id),
                                    data='{{"User": {{"CustomData" : {{"HiWatch Cert Number":"{}"}} }}}}'.format(cert_number),
                                    auth=(LOGIN, PASS) ,
                                    headers={'Content-Type': 'application/json'})
    return 0

def create_word_certificate(wb, type ='HCSA'):
    frame = pd.read_excel(wb)
    print(frame)
    for i, user_id in enumerate(frame['user_id']):
        cert_number = frame.loc[[i], ["Cert Number"]].to_string(header=False, index=False)
        type = frame.loc[[i], ["Type"]].to_string(header=False, index=False)
        type = type.strip()
        candidate_name = frame.loc[[i], ["Candidate name"]].to_string(header=False, index=False)
        email = frame.loc[[i], ["email"]].to_string(header=False, index=False)
        email= email.strip()
        valid = frame.loc[[i], ["Valid"]].to_string(header=False, index=False)

        if type == 'HiWatch':
            tpl = DocxTemplate(WORD_TEMPLATE_HIWATCH)
        else:
            tpl = DocxTemplate(WORD_TEMPLATE)
        context = {
            'Name': "{}".format(candidate_name),
            'Valid': valid[:10],
            'Number': cert_number,
            'Type': type
        }
        print(candidate_name)
        tpl.render(context)
        if not os.path.exists('./CertOut'):
            os.makedirs('./CertOut')
        tpl.save('./CertOut/{}.docx'.format(email))
        wd = os.getcwd()
        convert_to_pdf('{}/CertOut/{}.docx'.format(wd, email))
    return 0

def convert_to_pdf(filepath):
    """Save a pdf of a docx file."""
    try:
        word = client.DispatchEx("Word.Application")
        target_path = filepath.replace(".docx", r".pdf")
        word_doc = word.Documents.Open(filepath)
        word_doc.SaveAs(target_path, FileFormat=17)
        word_doc.Close()
    except Exception as e:
            raise e
    finally:
            word.Quit()

def send_email(To, filename):
    message = MIMEMultipart()
    message["From"] = FROM
    message["To"] = To
    message["Subject"] = SUBJECT

    body = "Добрый день. Еще раз поздравляем с успешным прохождением сертификации. Электронный сертификат во вложении." \
           " Если необходима печатная копия, пожалуйста сообщите"
    # Add body to email
    message.attach(MIMEText(body, "plain", 'utf-8'))

    with open(filename, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    context = ssl.create_default_context()
    #with smtplib.SMTP_SSL(SNMP_HOST, 465, context=context) as server:
    server = smtplib.SMTP(host=SNMP_HOST, port=587)
    server.starttls()
    server.login(FROM, PASSWORD_EMAIL)
    server.sendmail(FROM, [To, FROM], text)
        #server.quit()

def send_emails():
    file_list = [file for file in os.listdir('./CertOut/') if file.endswith('pdf')]
    for file in file_list:
        logging.debug('sending to {}'.format(file))
        send_email(file[:-4], './CertOut/{}'.format(file))
        logging.info('send to {} successful '.format(file[:-4]))
        time.sleep(60*2)
    return 0


if __name__ == '__main__':
    FROM = input("Type your e-mail and press enter:")
    PASSWORD_EMAIL = input("Type your pass and press enter:")
    report = []
    # переменная не обнуляется \ переписать
    #coursesReport(courses, date_from, date_to, report)


    #exel_to_lu('./Тестирование HCSA-AAI (non-video).xls')
    #create_word_certificate('./HCSA_28.xls')
    send_emails()




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


