from plotly.offline import plot
from plotly.graph_objs import Scatter, Bar
import pandas as pd
from ..models import *
import numpy as np


def prep_rcvd_data(qs, molecular_pos_tests, cases_with_mol_pos, outcome):

    outcome = str.lower(outcome)
    if outcome == 'probable' or outcome == 'confirmed':
        pass
    else:
        raise Exception('Invalid outcome variable passed to charts. '
                        'Values may only consist of "probable" or "confirmed".')

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
                  'hospitalized',
                  'icu',
                  ],
                 axis=1)

    df_pos_mol = pd.DataFrame.from_records(molecular_pos_tests[i].__dict__ for i in range(molecular_pos_tests.count()))
    df_pos_mol = df_pos_mol.drop(['_state',
                                  ],
                                 axis=1)

    print(f'DF positive {outcome} official tests: {df_pos_mol}')
    # df_pos_mol gives the expected output

    df_pos_mol_case = pd.DataFrame.from_records(
        cases_with_mol_pos[i].__dict__ for i in range(cases_with_mol_pos.count()))
    df_pos_mol_case = df_pos_mol_case.drop(['_state',
                                            'join_id',
                                            ],
                                           axis=1).drop_duplicates()
    print(f'DF for {outcome} cases with positives: {df_pos_mol_case}')
    # df_pos_mol_cases gives the expected output

    df_confirmed_notna = df[df[outcome].notna()]
    df_confirmed = df_confirmed_notna[df_confirmed_notna[outcome]]

    print(f'DF for cases marked {outcome}: {df_confirmed}')
    # df_confirmed has the expected output

    # df_probable_notna = df[df['probable'].notna()]
    # df_probable = df_probable_notna[df_probable_notna['probable']]

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
    print(f'Length: {len(df_test_data_case)}')
    print(f'DF test data joined to case id: {df_test_data_case}')
    # df_test_data_case gives the expected output

    df_pos_confirmed = df_test_data_case.join(df_confirmed.set_index('case_id'),
                                              how='inner',
                                              on='case_id').reset_index()

    print(f'DF case data joined to test data: {df_pos_confirmed}')

    # df_pos_confirmed gives the expected output
    df_pos_confirmed_rcvd = df_pos_confirmed.drop(['sample_date',
                                                   'result_date',
                                                   ],
                                                  axis=1).drop_duplicates()
    rcvd_prep = df_pos_confirmed_rcvd.groupby(df_pos_confirmed_rcvd['case_id']).apply(
        lambda x: x[x.rcvd_date == min(x.rcvd_date)])

    print(f'Prepared data: {rcvd_prep}')

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

    print(f'Missing_dates: {rcvd_missing_dates}')

    rcvd_rolling_avg_data = rcvd_rolling_avg_data.set_index('rcvd_date') \
        .sort_index() \
        .drop(['index'], axis=1)

    print(f'Rolling avg data: {rcvd_rolling_avg_data}')

    rcvd_rolling_avg_data = rcvd_rolling_avg_data.reindex(rcvd_missing_dates, fill_value=0)

    print(f'Reindexed data: {rcvd_rolling_avg_data}')
    print('Finished reindex')

    ROLLING_AVERAGE_WINDOW_SIZE = 7
    output = rolling_avg(rcvd_rolling_avg_data, ROLLING_AVERAGE_WINDOW_SIZE)

    # rolling_avg(df_pos_confirmed2)
    # rolling_avg(df_probable)
    return output


def rolling_avg(data, n):

    results = data.daily_cases.rolling(n).mean()

    print("Rolling avg results:")
    print(results)

    results = pd.DataFrame(results[n-1:])

    # print(results)

    output = rolling_avg_plot(results)
    return output


def rolling_avg_plot(data):
    plot_div = plot([Bar(x=data.index, y=data['daily_cases'])],
                    output_type='div')
    return plot_div


def prep_data_by_var(qs, pos_tests, cases_with_pos, outcome, group):
    from django.db.models import Prefetch

    cases = cases_with_pos.select_related('case__person', 'test')
    print(f'Cases: {cases}')
    persons = cases.all().values('case', 'case__person__sex', 'case__person__dob', 'test__rcvd_date')
    # print(f'Persons: {persons}')
    # df = pd.DataFrame.from_records(persons[i].__dict__ for i in range(persons.count()))
    df = pd.DataFrame.from_records(persons).drop_duplicates()
    # # persons = cases.select_related('person')
    print(f'Persons: {df}')
    #
    # outcome = str.lower(outcome)
    # if outcome == 'probable' or outcome == 'confirmed':
    #     pass
    # else:
    #     raise Exception('Invalid outcome variable passed to charts. '
    #                     'Values may only consist of "probable" or "confirmed".')
    #
    # df = pd.DataFrame.from_records(qs[i].__dict__ for i in range(qs.count()))
    #
    # # Drop irrelevant columns
    # df = df.drop(['_state',
    #               'test_id',
    #               'released_id',
    #               'old_case_no',
    #               'able_to_isolate_id',
    #               'text_follow_up',
    #               'email_follow_up',
    #               'monitor_not_case',
    #               'last_follow',
    #               'tent_release',
    #               'hospitalized',
    #               'icu',
    #               ],
    #              axis=1)
    #
    # df_pos_mol = pd.DataFrame.from_records(molecular_pos_tests[i].__dict__ for i in range(molecular_pos_tests.count()))
    # df_pos_mol = df_pos_mol.drop(['_state',
    #                               ],
    #                              axis=1)
    #
    # print(f'DF positive {outcome} official tests: {df_pos_mol}')
    # # df_pos_mol gives the expected output
    #
    # df_pos_mol_case = pd.DataFrame.from_records(
    #     cases_with_mol_pos[i].__dict__ for i in range(cases_with_mol_pos.count()))
    # df_pos_mol_case = df_pos_mol_case.drop(['_state',
    #                                         'join_id',
    #                                         ],
    #                                        axis=1).drop_duplicates()
    # print(f'DF for {outcome} cases with positives: {df_pos_mol_case}')
    # # df_pos_mol_cases gives the expected output
    #
    # df_confirmed_notna = df[df[outcome].notna()]
    # df_confirmed = df_confirmed_notna[df_confirmed_notna[outcome]]
    #
    # print(f'DF for cases marked {outcome}: {df_confirmed}')
    # # df_confirmed has the expected output
    #
    # # df_probable_notna = df[df['probable'].notna()]
    # # df_probable = df_probable_notna[df_probable_notna['probable']]
    #
    # # df_pos_confirmed = pd.merge(df_pos_mol_case,
    # #                             df_pos_mol,
    # #                             how='inner',
    # #                             on=['test_id'])
    # df_test_data_case = df_pos_mol_case.join(df_pos_mol.set_index('test_id'), lsuffix="DROP", how='inner', on='test_id')
    # df_test_data_case = df_test_data_case.drop(['test_id',
    #                                             'user_id',
    #                                             'result_id',
    #                                             'test_type_id',
    #                                             'source_id',
    #                                             'logged_date',
    #                                             'test_trace',
    #                                             ],
    #                                            axis=1) \
    #     .drop_duplicates() \
    #     .set_index('case_id')
    # print(f'Length: {len(df_test_data_case)}')
    # print(f'DF test data joined to case id: {df_test_data_case}')
    # # df_test_data_case gives the expected output
    #
    # df_pos_confirmed = df_test_data_case.join(df_confirmed.set_index('case_id'),
    #                                           how='inner',
    #                                           on='case_id').reset_index()
    #
    # print(f'DF case data joined to test data: {df_pos_confirmed}')
    #
    # # df_pos_confirmed gives the expected output
    # df_pos_confirmed_rcvd = df_pos_confirmed.drop(['sample_date',
    #                                                'result_date',
    #                                                ],
    #                                               axis=1).drop_duplicates()
    # rcvd_prep = df_pos_confirmed_rcvd.groupby(df_pos_confirmed_rcvd['case_id']).apply(
    #     lambda x: x[x.rcvd_date == min(x.rcvd_date)])
    #
    # print(f'Prepared data: {rcvd_prep}')
    #
    # rcvd_rolling_avg_data = rcvd_prep.groupby(rcvd_prep['rcvd_date']) \
    #     .apply(lambda j: j.assign(daily_cases=lambda x: x.case_id.nunique())) \
    #     .drop(['case_id',
    #            'person_id',
    #            'confirmed',
    #            'status_id',
    #            'iso_pcp',
    #            'reqs_pcp',
    #            'release_date',
    #            'rel_pcp',
    #            'active',
    #            'probable',
    #            'case_id',
    #            ],
    #           axis=1) \
    #     .reset_index() \
    #     .drop(['case_id',
    #            'level_1',
    #            ],
    #           axis=1) \
    #     .drop_duplicates() \
    #     .reset_index()
    #
    # rcvd_missing_dates = pd.date_range(min(rcvd_rolling_avg_data['rcvd_date']),
    #                                    max(rcvd_rolling_avg_data['rcvd_date']))
    #
    # print(f'Missing_dates: {rcvd_missing_dates}')
    #
    # rcvd_rolling_avg_data = rcvd_rolling_avg_data.set_index('rcvd_date') \
    #     .sort_index() \
    #     .drop(['index'], axis=1)
    #
    # print(f'Rolling avg data: {rcvd_rolling_avg_data}')
    #
    # rcvd_rolling_avg_data = rcvd_rolling_avg_data.reindex(rcvd_missing_dates, fill_value=0)
    #
    # print(f'Reindexed data: {rcvd_rolling_avg_data}')
    # print('Finished reindex')
    #
    # ROLLING_AVERAGE_WINDOW_SIZE = 7
    # output = rolling_avg(rcvd_rolling_avg_data, ROLLING_AVERAGE_WINDOW_SIZE)
    #
    # # rolling_avg(df_pos_confirmed2)
    # # rolling_avg(df_probable)
    # return output
    return