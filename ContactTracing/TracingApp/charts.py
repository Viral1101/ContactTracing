from plotly.offline import plot
from plotly.graph_objs import Scatter, Bar
import pandas as pd
import numpy as np


def prep_rcvd_data(qs, molecular_pos_tests, cases_with_mol_pos):

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

    df_pos_mol = pd.DataFrame.from_records(molecular_pos_tests[i].__dict__ for i in range(molecular_pos_tests.count()))
    df_pos_mol = df_pos_mol.drop(['_state',
                                  ],
                                 axis=1)

    # print("==DF positive molecular official tests==")
    # print(df_pos_mol)
    # df_pos_mol gives the expected output

    df_pos_mol_case = pd.DataFrame.from_records(
        cases_with_mol_pos[i].__dict__ for i in range(cases_with_mol_pos.count()))
    df_pos_mol_case = df_pos_mol_case.drop(['_state',
                                            'join_id',
                                            ],
                                           axis=1).drop_duplicates()
    # print("==DF for cases with molecular positive==")
    # print(df_pos_mol_case)
    # df_pos_mol_cases gives the expected output

    df_confirmed_notna = df[df['confirmed'].notna()]
    df_confirmed = df_confirmed_notna[df_confirmed_notna['confirmed']]

    # print("==DF for cases marked confirmed==")
    # print(df_confirmed)
    # df_confirmed has the expected output

    df_probable_notna = df[df['probable'].notna()]
    df_probable = df_probable_notna[df_probable_notna['probable']]

    # df_pos_confirmed = pd.merge(df_pos_mol_case,
    #                             df_pos_mol,
    #                             how='inner',
    #                             on=['test_id'])
    df_test_data_case = df_pos_mol_case.join(df_pos_mol.set_index('test_id'), lsuffix="DROP", how='inner', on='test_id')
    df_test_data_case = df_test_data_case.drop(['test_id',
                                                'user_id',
                                                'result_id',
                                                'test_type_id',
                                                'source_id',
                                                'logged_date',
                                                'test_trace',
                                                ],
                                               axis=1) \
        .drop_duplicates() \
        .set_index('case_id')
    # print('Length: %s' % len(df_test_data_case))
    # print("==DF test data joined to case id==")
    # print(df_test_data_case)
    # df_test_data_case gives the expected output

    df_pos_confirmed = df_test_data_case.join(df_confirmed.set_index('case_id'),
                                              how='inner',
                                              on='case_id').reset_index()

    # print("==DF confirmed case data joined to test data==")
    # print(df_pos_confirmed)
    # df_pos_confirmed gives the expected output
    df_pos_confirmed_rcvd = df_pos_confirmed.drop(['sample_date',
                                                   'result_date',
                                                   ],
                                                  axis=1).drop_duplicates()
    rcvd_prep = df_pos_confirmed_rcvd.groupby(df_pos_confirmed_rcvd['case_id']).apply(
        lambda x: x[x.rcvd_date == min(x.rcvd_date)])
    rcvd_rolling_avg_data = rcvd_prep.groupby(rcvd_prep['rcvd_date']) \
        .apply(lambda j: j.assign(daily_cases=lambda x: x.case_id.nunique())) \
        .drop(['case_id',
               'person_id',
               'confirmed',
               'status_id',
               'iso_pcp',
               'reqs_pcp',
               'release_date',
               'rel_pcp',
               'active',
               'probable',
               'case_id',
               ],
              axis=1) \
        .reset_index() \
        .drop(['case_id',
               'level_1',
               ],
              axis=1) \
        .drop_duplicates() \
        .reset_index()

    rcvd_missing_dates = pd.date_range(min(rcvd_rolling_avg_data['rcvd_date']),
                                       max(rcvd_rolling_avg_data['rcvd_date']))

    # print(rcvd_missing_dates)

    rcvd_rolling_avg_data = rcvd_rolling_avg_data.set_index('rcvd_date') \
        .sort_index() \
        .drop(['index'], axis=1)

    # print(rcvd_rolling_avg_data)

    rcvd_rolling_avg_data = rcvd_rolling_avg_data.reindex(rcvd_missing_dates, fill_value=0)
    # print(rcvd_rolling_avg_data)

    ROLLING_AVERAGE_WINDOW_SIZE = 7
    output = rolling_avg(rcvd_rolling_avg_data, ROLLING_AVERAGE_WINDOW_SIZE)

    # rolling_avg(df_pos_confirmed2)
    # rolling_avg(df_probable)
    return output


def rolling_avg(data, n):

    results = data.daily_cases.rolling(n).mean()

    results = pd.DataFrame(results[n-1:])

    # print(results)

    output = rolling_avg_plot(results)
    return output


def rolling_avg_plot(data):
    plot_div = plot([Bar(x=data.index, y=data['daily_cases'])],
                    output_type='div')
    return plot_div
