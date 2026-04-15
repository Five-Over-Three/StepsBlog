from flask import Flask, render_template, request
from wtforms import Form, validators, IntegerField, FloatField, DateField, TextAreaField
import pandas as pd
from datetime import datetime
import calendar
import plotly.graph_objects as pgo
import plotly.io as pio
from jinja2 import Template
from werkzeug.middleware.proxy_fix import ProxyFix
import math

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

#calendar data
col_names = [['year', 'month', 'day', 'steps', 'distance', 'pushups', 'situps', 'squats', 'weight', 'comment']]
date_format = '%Y-%m-%d'
calMonth = 4
calYear = 2026
myCal = calendar.Calendar()
myMonth = myCal.monthdayscalendar(calYear, calMonth)
monthName = calendar.month_name[calMonth]
days_in_month = calendar.monthrange(calYear, calMonth)[1]

#weight data
target_weight_start = 86.0
target_weight_tick = 0.07
target_weight = pd.Series([round(target_weight_start - x * target_weight_tick, 2) for x in range(days_in_month)], index=[x for x in range(1, days_in_month + 1)])

#prebuild chart stuffs where possible
yaxis = {
            'linewidth':2, 
            'showline':True, 
            'linecolor':'lightgrey', 
            'gridcolor':'antiquewhite',
            'range':[math.floor(target_weight_start - days_in_month * target_weight_tick) - 1, math.ceil(target_weight_start) + 1], 
            'dtick':0.5, 
            'ticklabelstep':2, 
            'title':{'text':'Kg'}
}
xaxis = {
            'linewidth':2, 
            'showline':True, 
            'linecolor':'lightgrey', 
            'gridcolor':'antiquewhite',
            'dtick':1, 
            'title':{'text':monthName + " " + str(calYear)}
}
layout = {'plot_bgcolor': 'floralwhite', 'paper_bgcolor': 'floralwhite', 'xaxis': xaxis, 'yaxis': yaxis} 
target_weight_chart = pgo.Scatter(x=target_weight.index, y=target_weight, line={'width':1, 'color':'darkgrey'}, name='Target weight')

@app.route('/')
def blog():
    #TODO - need homepage stuffs here e.g. link to latest post, calendar, graphs etc.
    steps_data = pd.read_csv("activitydata.csv")
    link_data = dict(zip(steps_data.loc[steps_data['month'] == calMonth, 'day'], steps_data.loc[steps_data['month'] == calMonth, 'steps']))

    #get weight data
    weight_index = steps_data.loc[(steps_data['year'] == 2026) & (steps_data['month'] == 4), 'day']
    weight_data = steps_data.loc[(steps_data['year'] == 2026) & (steps_data['month'] == 4), 'weight']
    actual_weight = pd.Series(weight_data)
    actual_weight.index = weight_index

    #build chart
    actual_weight_chart = pgo.Scatter(x=actual_weight.index, y=actual_weight, line={'shape':'spline', 'width':3, 'color':'darkred'}, mode='lines', name='Actual weight')
    chart = pgo.Figure([target_weight_chart, actual_weight_chart], layout=layout)
    input_template = 'templates/pre_chart.html'
    output_template = 'templates/chart.html'
    chart_data = {'chart': pio.to_html(chart, include_plotlyjs='cdn', full_html=False, div_id='weight_chart')}
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
