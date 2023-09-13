from datetime import date, timedelta
from django import forms
from django.db import models

# Import my own modules
from kisdb_connecting.operations import SelectAnswer, Queries


def converting(x):
    result = []
    for i in x:
        result.append((i, i))
    return tuple(result)


class DeptChoose(forms.Form):
    """ Represent drop-down list of departments name from KIS DB on the starting page. """
    # Create object that contains all departments from KIS DB and create list generator
    depts = SelectAnswer(query_text='SELECT name FROM mm.depts d').selecting()
    if type(depts) is str:
        pass
    else:
        str_values = [field[0] for field in depts]
        # Choice field on the page with ready drop-down list
        dept_name = forms.ChoiceField(label='Отделение', choices=converting(str_values),
                                      widget=forms.Select(attrs={'class': 'dept-custom'}))


class ResearchType(forms.Form):
    """ Represent drop-down list of research name from KIS DB on the starting page. """
    r_types = SelectAnswer(query_text='SELECT r_types FROM mm.depts d').selecting()
    if type(r_types) is str:
        pass
    else:
        str_values = [field[0] for field in r_types]
        research_types = forms.ChoiceField(label='Тип исследования', choices=converting(str_values))


class DateButtons(forms.Form):
    """ Represent buttons of date type on the page. It is the 3rd sql condition in query. """
    from_dt = forms.DateField(label='Начало периода',
                              initial=date.today() - timedelta(days=14),
                              widget=forms.SelectDateWidget(attrs={'class': 'datefield-custom'},
                                                            years=range(date.today().year, date.today().year-5, -1)
                                                            ),
                              )
    to_dt = forms.DateField(label='Конец периода',
                            initial=date.today(),
                            widget=forms.SelectDateWidget(attrs={'class': 'datefield-custom'},
                                                          years=range(date.today().year, date.today().year-5, -1)
                                                          ),
                            )

