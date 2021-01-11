import pandas as pd
from pathlib import Path
import fuzzymatcher
import recordlinkage
from .models import *
from datetime import datetime


def fuzzy_match(csv_file):

    address_join = pd.DataFrame(list(PersonAddressJoin.objects.values_list('person_id',
                                                                           'address_id')),
                                columns=["person_id",
                                         "address_id"])

    addresses = pd.DataFrame(list(Addresses.objects.values_list('address_id',
                                                                'street',
                                                                'street2',
                                                                'city',
                                                                'state',
                                                                'post_code',
                                                                )),
                             columns=['address_id',
                                      'street',
                                      'street2',
                                      'city',
                                      'state',
                                      'post_code',
                                      ])

    persons = pd.DataFrame(list(Persons.objects.values_list('person_id',
                                                            'first',
                                                            'mi',
                                                            'last',
                                                            'suffix',
                                                            'sex',
                                                            'dob',
                                                            'age',
                                                            )),
                           columns=['person_id',
                                    'first',
                                    'mi',
                                    'last',
                                    'suffix',
                                    'sex',
                                    'dob',
                                    'age',
                                    ])

    phone_join = pd.DataFrame(list(PersonPhoneJoin.objects.values_list('person_id',
                                                                       'phone_id',
                                                                       )),
                              columns=['person_id',
                                       'phone_id',
                                       ])

    phones = pd.DataFrame(list(Phones.objects.values_list('phone_id',
                                                          'phone_number',
                                                          )),
                          columns=['phone_id',
                                   'phone_number',
                                   ])

    # print(persons.head(5))

    personaddress = pd.merge(persons,address_join, on='person_id')
    personaddress2 = pd.merge(personaddress, addresses, on='address_id')

    personphone = pd.merge(personaddress2,phone_join, on='person_id')
    personphone2 = pd.merge(personphone,phones, on='phone_id')

    # print(personphone2.head(5))
    upload = pd.read_csv(csv_file, index_col=False)
    upload['DOB'] = pd.to_datetime(upload['DOB'], format='%m/%d/%Y')
    upload = upload.iloc[:, 0:13]

    print(upload.iloc[:, 0:13])

    indexer = recordlinkage.Index()
    indexer.full()

    patients = indexer.index(personphone2, upload)
    print(len(patients))

    compare = recordlinkage.Compare()
    compare.exact('city', 'City', label='City')
    compare.string('first',
                   'First Name',
                   threshold=0.85,
                   label='First_Name')
    compare.string('last',
                   'Last Name',
                   threshold=0.85,
                   label='Last_Name')
    compare.exact('dob',
                  'DOB',
                  label='DOB')
    compare.string('street',
                   'Street',
                   method='jarowinkler',
                   threshold=0.85,
                   label='Street')
    compare.string('street2',
                   'Street2',
                   method='jarowinkler',
                   threshold=0.85,
                   label='Street2')
    compare.exact('phone_number',
                  'Phone',
                  label='Phone')
    features = compare.compute(patients, personphone2,
                               upload)

    print(features.sum(axis=1).value_counts().sort_index(ascending=False))

    potential_matches = features[features.sum(axis=1) > 1].reset_index()
    print(potential_matches)
