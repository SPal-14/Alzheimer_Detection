import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog
from PyQt5.uic import loadUi
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
from PyQt5.QtCore import QTimer

class NameDialog(QDialog):
    def __init__(self, parent=None):
        super(NameDialog, self).__init__(parent)
        loadUi("name.ui", self)
        self.askName.clicked.connect(self.goToTest)

    def goToTest(self):
        name = self.nameinput.text()
        if name.strip() == "":
            QMessageBox.warning(self, "Missing Information", "Please enter your name.")
        else:
            self.close()
            mainWindow.takeTest(name)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("main.ui", self)
        self.saveChanges.clicked.connect(self.saveData)
        self.calendarWidget.clicked.connect(self.updatePlaceholders)
        self.takeTestButton.clicked.connect(self.showNameDialog)
        
        self.prev_name = ""
        self.prev_age = ""
        self.prev_gender = ""

        self.client = MongoClient('mongodb+srv://kolkatasouvik1:ODZgpn1SObDnrq5I@alzeimer.ote9ke6.mongodb.net/')
        self.db = self.client['Alzeimer_DB'] 
        self.collection = self.db['Daily_Updates']

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimerLabel)

        self.test_interface = None

    def updatePlaceholders(self):
        selected_date = self.calendarWidget.selectedDate().toString("dd-MM-yyyy")
        self.People_Met.setPlaceholderText("")
        self.Foods_Eaten.setPlaceholderText("")
        self.Places_Visited_2.setPlaceholderText("")
        self.Birthdays.setPlaceholderText(f"")
        self.Aniversaries.setPlaceholderText(f"")

    def saveData(self):
        if not self.Name.text() or not self.Age.text() or not self.Gender.text():
            QMessageBox.warning(self, "Missing Information", "Name, Age, and Gender are required.")
            return

        name = self.Name.text() 
        age = self.Age.text() 
        gender = self.Gender.text() 
        selected_date = self.calendarWidget.selectedDate().toString("dd-MM-yyyy")
        people_met = self.People_Met.text()
        foods_eaten = self.Foods_Eaten.text()
        places_visited = self.Places_Visited_2.text()
        birthdays = self.Birthdays.text()
        anniversaries = self.Aniversaries.text()

        if not people_met or not foods_eaten or not places_visited:
            QMessageBox.warning(self, "Missing Information", "Please fill in all required fields.")
            return

        record = {
            "name": name,
            "age": age,
            "gender": gender,
            "date": selected_date,
            "people_met": people_met,
            "foods_eaten": foods_eaten,
            "places_visited": places_visited,
            "birthdays": birthdays,
            "anniversaries": anniversaries
        }

        self.collection.insert_one(record)

        QMessageBox.information(self, "Success", "Details Saved Successfully!!")

    def showNameDialog(self):
        nameDialog = NameDialog(self)
        nameDialog.exec_()

    def takeTest(self, name):
        self.centralwidget.hide()
        
        if not self.test_interface:
            self.test_interface = loadUi("test_interface.ui", self)

        self.test_interface.show()
        self.submitButton.clicked.connect(lambda: self.submitAnswers(name))
        
        start_date = self.starting_date.date().toPyDate()
        end_date = self.ending_date.date().toPyDate()
        random_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        
        self.test_interface.testDate.setText(random_date.strftime("%d-%m-%Y"))
        self.updatePlaceholders()

        self.timer.start(5)

    def updateTimerLabel(self):
        remaining_time = self.timer.remainingTime()  
        seconds = remaining_time // 1000
        minutes = seconds // 60
        seconds %= 60
    
    def submitAnswers(self, name):
        test_ans = []

        print("Answers submitted:")
        
        test_ans.append(self.test_interface.lineEdit_Q1.text())
        test_ans.append(self.test_interface.lineEdit_Q2.text())
        test_ans.append(self.test_interface.lineEdit_Q3.text())
        test_ans.append(self.test_interface.lineEdit_Q4.text())
        test_ans.append(self.test_interface.lineEdit_Q5.text())

        QMessageBox.information(self, "Answers Submitted", "Your answers have been submitted.")
        self.test_interface.close()
        selected_date = self.test_interface.testDate.text()
        print("User :", name)
        print("Date for the test :",selected_date)
        query_result = self.collection.find_one({"$and": [{"name": name, "date" : selected_date}]})
        print(query_result)
        if query_result:
            db_values = [query_result["people_met"], query_result["foods_eaten"], 
                         query_result["places_visited"], query_result["birthdays"], 
                         query_result["anniversaries"]]
           
            correct_count = sum(1 for test, db_value in zip(test_ans, db_values) if test == db_value)
            print("Number of correct answers :", correct_count)

            percentage_correct = (correct_count / len(test_ans)) * 100
            print("Percentage of correct answers :", percentage_correct)

            if correct_count >= 4:
                severity = "Mildly Affected to Alzheimer"
            elif correct_count >= 2:
                severity = "Moderately Affected to Alzheimer"
            else:
                severity = "Severely Affected to Alzheimer"
            print("Severity of Alzheimer's :", severity)
            self.showResults(severity, percentage_correct)
        else:
            print("No data found for the selected date.")

        
    def showResults(self, severity, percentage_correct):
        dialog = QDialog(self)
        loadUi("results.ui", dialog)
        dialog.severityLabel.setText(f"Severity: {severity}")
        dialog.percentageLabel.setText(f"Percentage: {percentage_correct}%")
        dialog.closeButton.clicked.connect(dialog.close)
        dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
