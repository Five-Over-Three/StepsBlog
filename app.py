from flask import Flask, render_template, request
from wtforms import Form, validators, IntegerField, FloatField, DateField, TextAreaField
import pandas as pd
from datetime import datetime
import calendar
import plotly.graph_objects as go
import plotly.io as io
from jinja2 import Template
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

class UploadForm(Form):
    date = DateField('Date', [validators.InputRequired()])
    steps = IntegerField('Steps', [validators.InputRequired()])
    distance = IntegerField('Distance', [validators.InputRequired()])
    pushups = IntegerField('Push-ups', [validators.InputRequired()])
    situps = IntegerField('Sit-ups', [validators.InputRequired()])
    squats = IntegerField('Squats', [validators.InputRequired()])
    weight = FloatField('Weight', [validators.InputRequired()])
    comment = TextAreaField('Comment', [validators.InputRequired()])

form = UploadForm()

#set up to write data
col_names = [['year', 'month', 'day', 'steps', 'distance', 'pushups', 'situps', 'squats', 'weight', 'comment']]
date_format = '%Y-%m-%d'
calMonth = 4
calYear = 2026
myCal = calendar.Calendar()

@app.route('/')
def blog():
    #TODO - need homepage stuffs here e.g. link to latest post, calendar, graphs etc.
    myMonth = myCal.monthdayscalendar(calYear, calMonth)
    steps_data = pd.read_csv("activitydata.csv")
    monthName = calendar.month_name[calMonth]
    link_data = dict(zip(steps_data.loc[steps_data['month'] == calMonth, 'day'], steps_data.loc[steps_data['month'] == calMonth, 'steps']))
    print(link_data)

    #add chart to the template
    targetWeight = [round(85.6 - 0.07 * x, 2) for x in range(30)]
    actualWeight = [85.6, 85.7, 85.4]
    date = [x+1 for x in range(30)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=date, y=targetWeight, mode='lines', name='Target weight', line={'color':'rgb(211,211,211)'}, zorder=1))
    fig.add_trace(go.Scatter(x=date, y=actualWeight, mode='lines', name='Actual weight', line={'color':'rgb(139,0,0)', 'shape':'spline'}, zorder=2))
    fig.update_layout({'xaxis':{'tick0':1, 'dtick':1, 'title':{'text':'April 2026'}, 'zerolinecolor':'rgb(139,0,0)', 'zerolinewidth':5, 'zeroline':True, 'visible':True}, 'yaxis':{'tick0':82, 'dtick':1, 'range':[82,87], 'title':{'text':'Weight (kg)'}}})
    input_template = 'templates/pre_chart.html'
    output_template = 'templates/chart.html'
    chart_data = {'chart': io.to_html(fig, include_plotlyjs='cdn', full_html=False, div_id='weight_chart')}
    with open(output_template, 'w', encoding='utf-8') as output_file:
        with open(input_template) as input_file:
            j2_template = Template(input_file.read())
            output_file.write(j2_template.render(chart_data))

    return render_template('index.html', monthName=monthName, calMonth=calMonth, calYear=calYear, myMonth=myMonth, link_data=link_data)

@app.route('/<int:year>/<int:month>/<int:day>')
def show_day(year, month, day):
    #TODO - validate the inputs, serve page if ok, error if not
    day_name = calendar.day_name[calendar.weekday(year, month, day)]
    month_name = calendar.month_name[month]

    #read data from csv file
    activity_data = pd.read_csv('activitydata.csv')

    #get relevant data from dataframe and pass to render template
    display_data = activity_data.query('year == @year and month == @month and day == @day')
    display_data.reset_index(drop=True, inplace=True)
    return render_template('blog.html', display_data=display_data, day_name=day_name, month_name=month_name)

@app.route('/upload', methods=['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        #create dataframe and write to file
        data_series = [
            datetime.strptime(request.form['date'], date_format).year,
            datetime.strptime(request.form['date'], date_format).month,
            datetime.strptime(request.form['date'], date_format).day,
            request.form['steps'],
            request.form['distance'],
            request.form['pushups'],
            request.form['situps'],
            request.form['squats'],
            request.form['weight'],
            request.form['comment']
        ]
        upload_data = pd.DataFrame([data_series], columns=col_names)
        upload_data.to_csv('activitydata.csv', mode='a', index=False, header=False)

        #TODO - parse comment data into html using <p> and <br> to keep the csv looking nice (use regex?)
        #need proper tests here to prevent duplication or overwriting of existing data

        #TODO - how to deal with missing data. currently all entries have at least steps & distance, but may not in the future, so need to have a way to cleanly handle this, both in the body content and in the date picker.
        
        return render_template('uploaded.html', form=form)
    else:
        return render_template('input.html', form=form)

# if __name__ == '__main__':
#     app.run(debug=True)
