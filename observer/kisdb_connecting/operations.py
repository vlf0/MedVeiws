import re
import pandas as pd
import psycopg2
from psycopg2 import Error
from datetime import datetime, timedelta
from WebApp.models import ConnectingToKIS
from . import string_snippets


today = datetime.today()
three_days = timedelta(days=3, hours=0, minutes=0, microseconds=0, milliseconds=0)


def dates(x):
    x = datetime.strftime(x, '%d.%m.%Y %H:%M:%S')
    dt, tm = x.split(' ')
    result = '-'.join(dt.split('-')[::-1]) + ' ' + str(tm)
    return result


class ReportExcelWriter:
    """ Applying styles to dataframe going to excel file.
    Has two methods for two different reports. """
    @staticmethod
    def xlsx_styles_researches(dept_name, frame):
        writer = pd.ExcelWriter(fr'./WebApp/static/reports/rep_{dept_name}.xlsx',
                                date_format='dd.mm.yyyy', datetime_format='dd.mm.yyyy')
        frame.to_excel(excel_writer=writer, sheet_name='Отчёт', engine='xlsxwriter', index=False)
        writer.sheets['Отчёт'].set_column(0, 0, 45)
        writer.sheets['Отчёт'].set_column(1, 1, 10)
        writer.sheets['Отчёт'].set_column(2, 3, 45)
        writer.sheets['Отчёт'].set_column(4, 5, 22)
        writer.sheets['Отчёт'].set_column(6, 6, 10)
        writer.close()

    @staticmethod
    def xlsx_styles_epicrisis(dept_name, frame):
        writer = pd.ExcelWriter(fr'./WebApp/static/reports/rep_{dept_name}.xlsx',
                                date_format='dd.mm.yyyy', datetime_format='dd.mm.yyyy')
        frame.to_excel(excel_writer=writer, sheet_name='Отчёт', engine='xlsxwriter', index=False)
        writer.sheets['Отчёт'].set_column(0, 0, 5)
        writer.sheets['Отчёт'].set_column(1, 1, 45)
        writer.sheets['Отчёт'].set_column(2, 2, 10)
        writer.sheets['Отчёт'].set_column(3, 3, 45)
        writer.sheets['Отчёт'].set_column(4, 5, 20)
        writer.sheets['Отчёт'].set_column(6, 6, 5)
        writer.close()


class Queries:
    """ This object consists of gotten values from web pages
     and returns full query in string format ready to use in DB. """
    types_converting = {
        'Лабораторные исследования': 1,
        'Инструментальные исследования': 2,
        'Процедуры и манипуляции': 3,
        'Операции': 4,
        'Консультации': 5,
        'Невыгруженные эпикризы': 7
    }

    def __init__(self, dept, research, from_dt, to_dt):
        self.dept = dept
        self.research = research
        self.from_dt = from_dt
        self.to_dt = to_dt

    def ready_select(self):
        if self.types_converting[self.research] == 7:
            return f'SELECT pat_fio, pat_ib, sign_dt, pat_leave_dt FROM mm.tap' \
                   f' WHERE sign_dt between \'{self.from_dt}\' and \'{self.to_dt}\''
        else:
            return f'select doc_fio, ib_num, pat_fio, research, create_dt, plan_dt, status FROM mm.dbkis' \
                   f' WHERE dept = \'{self.dept}\' AND r_type = \'{self.types_converting[self.research]}\'' \
                   f' AND create_dt between \'{self.from_dt}\' and \'{self.to_dt}\''


class SelectAnswer:
    """ Represent SQL query object in the text format. """
    def __init__(self, query_text):
        self.query_text = query_text

    def selecting(self):
        """ Connecting to DB and execute SQL query. If connect not established or
        bad query getting - throw exceptions that displaying on the web page. """
        if len(ConnectingToKIS.objects.all()) != 0:
            actual_db = ConnectingToKIS.objects.filter(active='True').values()
            if len(actual_db) == 1:
                actual_db = actual_db[0]
                try:
                    connection = psycopg2.connect(database=actual_db['db'],
                                                  host=actual_db['host'],
                                                  #   port=5431,
                                                  port=actual_db['port'],
                                                  user=actual_db['user'],
                                                  password=actual_db['password'])
                    try:
                        cursor = connection.cursor()
                        cursor.execute(self.query_text)
                        selecting_data = cursor.fetchall()
                        return selecting_data
                    except (Exception, Error) as e:
                        return f'Ошибка в SQL запросе!\n\n{e}\n'
                    finally:
                        cursor.close()
                        connection.close()
                except (Exception, Error) as e:
                    return f'Ошибка подключения к БД!\n\n{e}\n'
            elif len(actual_db) > 1:
                return 'There are more than one DataBases in ACTIVE status!\n' \
                       ' Check DB in active in the admin panel!'
            else:
                return 'DB not active!\n To use it - turn on check box in the admin panel!'
        else:
            return 'There are no any records in the BD data tab!'


class ReadyReport:
    """ Represent HTML page and contains selected required data.
    The data converts to HTML code by Pandas DataFrame. Data for connecting get from app DB models. """
    def __init__(self, db_data):
        self.db_data = db_data
        if type(self.db_data) is str:
            self.dataframe = f'\t<p class="center-top-text">{self.db_data}</p>\n'
        elif type(self.db_data) is list and len(self.db_data) == 0:
            self.dataframe = string_snippets.tab_done
        else:
            row_values = len(self.db_data[0])
            rows_number = len(self.db_data)
            # List of lists of data separated and grouped inside
            data_lists = [list(map(lambda x: x[i], self.db_data)) for i in range(row_values)]
            # DataFrame's headers names for all type of researches
            headers_names = ['Врач', 'Номер ИБ', 'Пациент', 'Назначение',
                             'Дата создания', 'Назначено на дату', 'Статус']
            # 5 values in 1 row - if user chosen "Невыгруженные эпикризы"
            if row_values == 4:
                headers_names = ['ID', 'ФИО пациента', 'ИБ пациента',
                                 'Дата подписи выписного эпикриза', 'Дата выписки пациента']
                # Adding column with ID's
                data_lists.insert(0, [i for i in range(1, rows_number + 1)])
            # 5 values in 1 row - if user chosen "Невыгруженные эпикризы по всем отделениям"
            elif row_values == 6:
                headers_names = ['ID', 'ФИО пациента', 'ИБ пациента', 'Заведующий отделением',
                                 'Дата подписи выписного эпикриза', 'Дата выписки пациента', 'Отделение']
                # Adding column with ID's
                data_lists.insert(0, [i for i in range(1, rows_number + 1)])
            # Creating dict for DataFrame
            data = dict(zip(headers_names, data_lists))
            df = pd.DataFrame(data=data, index=range(1, rows_number + 1))
            second_column_name = df.columns[1]
            if second_column_name == 'ФИО пациента' and len(df.columns) == 5:
                col_num = 5
            elif second_column_name == 'ФИО пациента' and len(df.columns) == 7:
                col_num = 6
            # Adding new column contains the different between today and sign date in DF
            df.insert(loc=col_num, column='Не выгружено',
                      value=(today - df['Дата выписки пациента'].array).days)
            df.sort_values(by=['Не выгружено'], ascending=False, inplace=True)
            if second_column_name == 'Номер ИБ':
                df.columns.rename('ID', inplace=True)
            self.dataframe = df

    def to_excel(self, dept):
        if type(self.dataframe) is not str:
            first_column_name = self.dataframe.columns[0]
            if first_column_name == 'ID':
                ReportExcelWriter.xlsx_styles_epicrisis(dept_name=dept, frame=self.dataframe)
            else:
                ReportExcelWriter.xlsx_styles_researches(dept_name=dept, frame=self.dataframe)
        return

    def to_html(self, error_value=None):
        """ Prepare raw data getting from KIS DB and creating HTML template based on them. Data handled by PANDAS. """
        if error_value:
            # Date validations error text instead data table
            tab = string_snippets.date_validation_error
            # Editing strings of html template
            string_snippets.top_of_template = string_snippets.top_of_template\
                .replace('<br><br>Невыполненные {{chosen_type}} за перод с {{from_dt}} по {{to_dt}}', '')
        elif type(self.dataframe) is str:
            tab = self.dataframe
        else:
            first_column_name = self.dataframe.columns[0]
            if first_column_name == 'ID':
                # Applying format to cells by condition
                report = self.dataframe.to_html(formatters=
                                        {
                                            # Formatting dates to string
                                            'Дата подписи выписного эпикриза': dates,
                                            'Дата выписки пациента': dates,
                                            # Formatting row by condition
                                            'ID': lambda x: f'over{x}'
                                            if (today - self.dataframe.at[x, 'Дата выписки пациента'])
                                            > three_days else f'{x}',

                                            # Dates formatting a newer column "Не выгружено"
                                            # 'Не выгружено': lambda y: f'center{y}' if y == 'Подписано будущей датой'
                                            # else ''
                                            
                                            'Не выгружено': lambda y: f'center{y} дней' if y not in [1, 2, 3, 4]
                                            or y in list(range(11, 21)) and str(y)[-1] not in ['1', '2', '3', '4']
                                            else f'center{y}'
                                                 
                                            f' день' if y == 1 else f'center{y}' f' дня' if y in [2, 3, 4]
                                            and str(y)[-1] in ['2', '3', '4'] and y not in list(range(11, 21)) else ''
                                        },
                                        justify='center', index=False)
                report = report.replace('<td>center', '<td style="text-align: center;">')
                # Changing color and style in the all ID's cells
                report = re.sub(r'<tr>\s*<td>', '<tr>\n\t  <td bgcolor="#F6BD8E" style="text-align: center;">',
                                report)
                # Applying entire row color style where is text "over" (it is condition for dates comparison)
                report = re.sub(r'<tr>\s*<td bgcolor="#F6BD8E" style="text-align: center;">over',
                                '<tr bgcolor="yellow">\n\t  <td bgcolor="#F6BD8E" style="text-align: center;">',
                                report)
                tab = string_snippets.tab_report_epicrisis + string_snippets.download_button +\
                      string_snippets.tab_table + report + string_snippets.tab_table_end

            else:
                report = self.dataframe.to_html(justify="center", formatters={'Дата создания': dates,
                                                                              'Назначено на дату': dates})
                # Adding own class for further applying css for column "ID"
                report = re.sub(r'<tr style="text-align: center;">\s*<th>ID',
                                '<tr style="text-align: center;">\n\t  <th class="index-name">ID', report)
                # Result of creating dataframe and formatting to HTML
                tab = string_snippets.tab_report + string_snippets.download_button +\
                      string_snippets.tab_table + report + string_snippets.tab_table_end
            # Create common SIMI report
            if len(self.dataframe.columns) == 8:
                return report
        # Create output.html
        with open('./WebApp/templates/output.html', 'wt',
                  encoding='utf-8') as template:
            template.write(string_snippets.top_of_template)
            template.writelines(tab)
            template.writelines(string_snippets.bot_of_template)
