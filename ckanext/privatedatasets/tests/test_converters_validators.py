import unittest
import ckanext.privatedatasets.converters_validators as conv_val

from mock import MagicMock
from nose_parameterized import parameterized


class ConvertersValidatorsTest(unittest.TestCase):

    def setUp(self):
        # Create mocks
        self._toolkit = conv_val.toolkit
        conv_val.toolkit = MagicMock()

        self._db = conv_val.db
        conv_val.db = MagicMock()

    def tearDown(self):
        conv_val.db = self._db
        conv_val.toolkit = self._toolkit

    @parameterized.expand([
        # When no data is present, no errors should be returned
        (True,    True,  'conwet', '',     False),
        ('True',  True,  'conwet', '',     False),
        (False,   True,  'conwet', '',     False),
        ('False', True,  'conwet', '',     False),
        (None,    True,  'conwet', '',     False),
        (None,    False, 'conwet', '',     False),
        (True,    True,  None,     '',     False),
        ('True',  True,  None,     '',     False),
        (False,   True,  None,     '',     False),
        ('False', True,  None,     '',     False),
        (None,    True,  None,     '',     False),
        (None,    False, None,     '',     False),
        # When data is present, the field is only valid when the
        # the private field is set to true (organization should
        # not be taken into account anymore)
        (True,    True,  'conwet', 'test', False),
        ('True',  True,  'conwet', 'test', False),
        (True,    False, 'conwet', 'test', False),
        ('True',  False, 'conwet', 'test', False),
        (False,   True,  'conwet', 'test', True),
        ('False', True,  'conwet', 'test', True),
        (False,   False, 'conwet', 'test', True),
        ('False', False, 'conwet', 'test', True),
        (None,    True,  'conwet', 'test', False),
        (None,    False, 'conwet', 'test', True),
        (True,    True,  None,     'test', False),
        ('True',  True,  None,     'test', False),
        (True,    False, None,     'test', False),
        ('True',  False, None,     'test', False),
        (False,   True,  None,     'test', True),
        ('False', True,  None,     'test', True),
        (False,   False, None,     'test', True),
        ('False', False, None,     'test', True),
        (None,    True,  None,     'test', False),
        (None,    False, None,     'test', True),
    ])
    def test_metadata_checker(self, received_private, package_private, owner_org, metada_val, error_set):

        # Configure the mocks
        package_show = MagicMock(return_value={'private': package_private, 'id': 'package_id'})
        conv_val.toolkit.get_action = MagicMock(return_value=package_show)

        KEY = ('test',)
        errors = {}
        errors[KEY] = []

        data = {}
        data[('id',)] = 'package_id'
        data[('owner_org',)] = owner_org
        if received_private is not None:
            data[('private',)] = received_private
        data[KEY] = metada_val

        conv_val.private_datasets_metadata_checker(KEY, data, errors, {})

        if error_set:
            self.assertEquals(1, len(errors[KEY]))
        else:
            self.assertEquals(0, len(errors[KEY]))

    @parameterized.expand([
        ('',             0, []),
        ('',             2, []),
        ('a',            0, ['a']),
        ('a',            2, ['a']),
        (',,,   , ,  ',  0, []),
        (',,,   , ,  ',  2, []),
        ('a,z, d',       0, ['a', 'z', 'd']),
        ('a,z, d',       2, ['a', 'z', 'd']),
        (['a','z', 'd'], 0, ['a', 'z', 'd']),
        (['a','z', 'd'], 2, ['a', 'z', 'd']),
    ])
    def test_allowed_user_convert(self, users, previous_users, expected_users):
        key_str = 'allowed_users_str'
        key = 'allowed_users'

        # Configure mock
        name_validator = MagicMock()
        conv_val.toolkit.get_validator = MagicMock(return_value=name_validator)
        
        # Fullfill the data dictionary
        # * list should be included in the allowed_users filed
        # * strings should be included in the allowed_users_str field
        if isinstance(users, basestring):
            data_key = key_str
        else:
            data_key = key

        data = {(data_key,): users}

        for i in range(0, previous_users):
            data[(key, i)] = i

        # Call the function
        context = {'user': 'test', 'auth_obj_id': {'id': 1}}
        conv_val.allowed_users_convert((key,), data, {}, context)

        # Check that the users are set properly
        for i in range(previous_users, previous_users + len(expected_users)):
            name_validator.assert_any_call(expected_users[i - previous_users], context)
            self.assertEquals(expected_users[i - previous_users], data[(key, i)])

    @parameterized.expand([
        ([],),
        (['a'],),
        (['a', 'b'],),
        (['a', 'b', 'c'],),
        (['a', 'b', 'c', 'd', 'e'],)
    ])
    def test_get_allowed_users(self, users):
        key = 'allowed_users'
        data = {('id',): 'package_id'}

        # Create the users
        db_res = []
        for user in users:
            db_row = MagicMock()
            db_row.package_id = 'package_id'
            db_row.user_name = user
            db_res.append(db_row)

        conv_val.db.AllowedUser.get = MagicMock(return_value=db_res)

        # Call the function
        context = {'model': MagicMock()}
        conv_val.get_allowed_users((key,), data, {}, context)

        # Check that the users are set properly
        for i, user in enumerate(users):
            self.assertEquals(user, data[(key, i)])

        # Check that the table has been initialized properly
        conv_val.db.init_db.assert_called_once_with(context['model'])
