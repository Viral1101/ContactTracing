# Process the statistics
# Charts wanted:
#   Confirmed cases by age, sex, zip
#   7-day rolling average of cases, with danger line
#   Total cases per day; reported, first_sx/sample_date

import pandas as pd


def covid_stats(qs):

    # Convert the queryset into a dataframe
    df = pd.DataFrame.from_records(qs[i].__dict__ for i in range(qs.count()))
    # Drop irrelevant columns
    df = df.drop(['_state',
                  'test_id',
                  'released_id',
                  'old_case_no',
                  'able_to_isolate_id',
                  'text_follow_up',
                  'email_follow_up',
                  'monitor_not_case',
                  'last_follow',
                  'tent_release',
                  ],
                 axis=1)

    confirmed_cases = df.loc[df['confirmed'] == 1]
    confirmed_sex = counts(confirmed_cases, 'sex')
    confirmed_hospitalized = counts(confirmed_cases, 'hospitalized')
    confirmed_icu = counts(confirmed_cases, 'icu')
    confirmed_count = counts(confirmed_cases, 'confirmed')

    probable_cases = df.loc[df['probable'] == 1]
    probable_sex = counts(probable_cases, 'sex')
    probable_count = counts(probable_cases, 'probable')


def counts(data, variable):

    count_data = data.groupby[variable].size().reset_index(name='counts')

    return count_data