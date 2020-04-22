import sys  # sys нужен для передачи argv в QApplication
import os  # Отсюда нам понадобятся методы для отображения содержимого директорий
from PyQt5 import QtWidgets, QtCore
import design
import main_backend
import xlwt

#os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
#os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(os.getcwd(), 'plugins', 'platforms')
#os.environ['QT_DEBUG_PLUGINS'] = '1'


class ExampleApp(QtWidgets.QMainWindow, design.Ui_Dialog):
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.py
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна

        self.pushButton.clicked.connect(self.generate_report)
        self.pushButton_2.clicked.connect(self.selectFile)
        self.pushButton_3.clicked.connect(self.send_report)
        self.pushButton_4.clicked.connect(self.generate_certificate)
        self.pushButton_5.clicked.connect(self.send_emails)

    def selectFile(self):
        print("choose input file 1")
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Open new file", '.', "(*.xls*)")
        self.lineEdit_3.setText("{}".format(file[0]))
        print(file[0])
        return file[0]

    def send_report(self):
        print( self.lineEdit_3.text())
        main_backend.exel_to_lu(self.lineEdit_3.text())
        return 0
    def generate_report(self):
        report = []
        courses = []
        if self.radioButton.isChecked():
            courses = main_backend.courses_HCSA
        if self.radioButton_2.isChecked():
            courses = main_backend.courses_HCSA_AAI
        if self.radioButton_3.isChecked():
            print('HCSA-VMS')
        if self.radioButton_4.isChecked():
            courses = main_backend.courses_HCSP
        if self.radioButton_5.isChecked():
            courses = main_backend.courses_HiWatch
        if courses is not None:
            wb = main_backend.coursesReport(courses, self.dateEdit.text(), self.dateEdit_2.text(), report, transliterate=self.checkBox.isChecked())
            filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', '', ".xls(*.xls)")
            wb.save(filename[0])
        return 0
    def generate_certificate(self):
        print('start generating certificates')
        if self.radioButton_5.isChecked():
            type = main_backend.courses_HiWatch[0]['type']
        else:
            type = 'HCSA'
        print(type)
        main_backend.create_word_certificate(self.lineEdit_3.text(), type=type)
        return 0
    def send_emails(self):
        print('sending emails ....')
        main_backend.FROM = self.lineEdit_4.text()
        main_backend.PASSWORD_EMAIL = self.lineEdit_5.text()
        print(main_backend.FROM)
        print(main_backend.PASSWORD_EMAIL)
        main_backend.send_emails()
        return 0





  #          frame1 = readnaryad(naryad, NAMES1, skiprows=17)
  #          frame2 = readframe2(file2, NAMES2, skiprows=1)
  #          row_number = frame1.shape[0]

  #          for row_numb in range(row_number):
   #             buisnes_trip_report(template, frame1, frame2, row_numb)

def main_UI():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение

#if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
#    main_UI()  # то запускаем функцию main()

main_UI()
