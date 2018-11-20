import MySQLdb, re
from flask import Flask, render_template, request
from html import unescape
from authentification1 import *

app = Flask(__name__)


def handle_spaces(string):
    return re.sub(' +', ' ', string).strip()


def quote(x):
    return "'"+x+"'"


def connect():
    connection = MySQLdb.connect(user=user, password=password,
                                 db = db, use_unicode=True)
    connection.encoding = 'utf-8'
    return connection


def get_id_count(table):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute(f"SELECT COUNT(id) FROM {table};")
    res = cursor.fetchone()[0]
    i = int(res)
    connection.close()
    return i


def new_record(form):
    connection = connect()
    cursor = connection.cursor()
    table = form.pop('table')
    fields = ','.join([str(i) for i in form])
    values = ','.join([quote(str(form[i])) for i in form])
    query = f"INSERT INTO {table}({fields}) VALUES ({values});"
    print(query)
    cursor.execute(query)
    connection.commit()
    connection.close()


def change_record(form):
    connection = connect()
    cursor = connection.cursor()
    table_name = form.pop('table')
    rowId = form.pop('id')
    setting = ""
    for key, val in form.items():
        setting += f"{key} = '" + val + "', "
    setting = setting.strip(', ')
    query = f"UPDATE {table_name} SET " + setting + "WHERE id = " + rowId + ";"
    cursor.execute(query)
    connection.commit()
    connection.close()


def select_record(form):
    connection = connect()
    cursor = connection.cursor()
    table = form['table']
    record_id = form['id']
    query = f"SELECT * FROM {table} WHERE id={record_id};"
    print(query)
    cursor.execute(query)
    record = cursor.fetchone()
    connection.close()
    col_names = get_col_names(table)
    record = {col_names[i]: record[i] for i in range(len(col_names))}
    return record


def delete_record(table, record_id):
    connection = connect()
    cursor = connection.cursor()
    query = f"DELETE FROM {table} WHERE id={record_id};"
    cursor.execute(query)
    connection.commit()
    connection.close()


def get_table_as_markup(table_name):
    table_data = get_table_data(table_name)
    col_names = get_col_names(table_name)
    return render_template('response.html', selected_table = table_data,
    col_names = col_names)


def get_table_data(table_name):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table_name};")
    table_data = cursor.fetchall()
    connection.close()
    return table_data


def get_table_options():
    connection = connect()
    cursor = connection.cursor()
    cursor.execute('SHOW TABLES;')
    output = [i[0] for i in cursor.fetchall()]
    connection.close()
    return output


def get_col_names(table_name):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute(f"desc {table_name};")
    col_names = [i[0] for i in cursor.fetchall()]
    connection.close()
    return col_names


@app.route('/createRecord', methods = ['GET', 'POST'])
def create_record():
    if request.method == 'GET' and request.args:
        return render_template('data_form.html', fields=get_col_names(request.args['table'])[1:], record=None,
        table = request.args['table'], id_value = get_id_count(request.args['table'])+1)
    if request.method == 'POST' and request.form:
        new_record(request.form.to_dict())
        return "Success"


@app.route('/alterRecord', methods = ['GET', 'POST'])
def alter_record():
    if request.method == 'GET' and request.args:
        record = select_record(request.args)
        return render_template('data_form.html', fields=None, record=record, table=request.args['table'],
        id_value = None)
    if request.method == 'POST' and request.form:
        change_record(request.form.to_dict())
        return "Success"


@app.route('/')
def display_data():
    if request.method == 'GET' and request.args:
        if request.args['action'] == 'getTable':
            tablename = request.args['table']
            return get_table_as_markup(tablename)
        elif request.args['action'] == 'deleteRow':
            tablename = request.args['table']
            row_id = request.args['id']
            delete_record(tablename, row_id)
            return "Success"
    return render_template("index.html", table_options = get_table_options(), col_names = get_col_names('students'),
    selected_table = get_table_data('students'), search_options=('Студент','Задание','Контрольная'))


@app.route('/search', methods=["GET","POST"])
def search():
    if request.form:
        category = unescape(request.form['category'])
        query_text = handle_spaces(unescape(request.form['query']))
        if category == 'Студент':
            col_names = get_col_names('students')
            query = f'''SELECT * FROM students WHERE CONCAT(name, ' ',
            patername, ' ', familyname, ' ', name, ' ', patername)
            LIKE '%{query_text}%' OR CONCAT(name, ' ', familyname)
            LIKE '%{query_text}%';'''
        elif category == 'Задание':
            col_names = get_col_names('question')
            query = f'''SELECT * FROM question WHERE question_text LIKE '%{query_text}%';'''
        elif category == "Контрольная":
            col_names = get_col_names('test')
            query = f'''SELECT * FROM test WHERE title LIKE '%{query_text}%';'''
        connection = connect()
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        return render_template('search_results.html', result=result,
        col_names = col_names, search_options=('Студент','Задание','Контрольная'))


@app.route('/studentstats')
def show_studentstats():
    connection = connect()
    cursor = connection.cursor()
    cursor.execute('''SELECT students.id, students.familyname,
    students.name, students.patername, students.AcGroup,
    test.id, test.title, test.passdate, mark.mark FROM students INNER JOIN
    mark ON students.id = mark.student_id INNER JOIN test
    ON mark.test_id = test.id ORDER BY test.passdate;''')
    stats = cursor.fetchall()
    connection.close()
    return render_template('studentstats.html', table=stats,
                           fields = ('ID студента',
                                     'Фамилия',
                                     'Имя',
                                     'Отчество',
                                     'Группа',
                                     'ID контрольной',
                                     'Название контрольной',
                                     'Дата',
                                     'Оценка'))


if __name__ == '__main__':
    app.run(debug=True)