from flask import Flask, render_template
import calendar

app = Flask(__name__)

@app.route('/')
def cal_tesxt():
    return render_template('calendarTest.html')

@app.route('/<int:year>/<int:month>/<int:day>')
def show_day(year, month, day):
    month_name = calendar.month_name[month]
    day_name = calendar.day_name[calendar.weekday(year, month, day)]
    return render_template('day_test.html', year=year, month_name=month_name, day=day, day_name=day_name)

if __name__ == '__main__':
    app.run(debug=True)