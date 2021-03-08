import pandas as pd


# Accept a queryset from COVID DB and process into a panda and feed
# formatted data to generate charts. Return the charts to be rendered by the view.
def queryset_to_charts(qs, tests):

    df_cases = pd.DataFrame.from_records(qs[i].__dict__ for i in range(qs.count()))

    # Drop irrelevant columns
    df_cases = df_cases.drop(['_state',
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

    df_tests = pd.DataFrame.from_records(tests[i].__dict__ for i in range(tests.count()))

    print(f'{df_tests.columns}')

    df_tests = df_tests.drop(['_state',
                              'join_id',
                              ])


