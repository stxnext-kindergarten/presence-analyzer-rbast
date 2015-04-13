# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday/')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_api_mean_time_weekday_404(self):
        """
        Test response of mean presence time for a nonexistent user.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/0')
        self.assertEqual(resp.status_code, 404)

    def test_api_mean_time_weekday(self):
        """
        Test mean presence time of given user grouped by weekday.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertEqual(
            data,
            [
                [u'Mon', 0],
                [u'Tue', 30047.0],
                [u'Wed', 24465.0],
                [u'Thu', 23705.0],
                [u'Fri', 0],
                [u'Sat', 0],
                [u'Sun', 0]
            ]
        )

    def test_api_presence_weekday_404(self):
        """
        Test response of total presence time for a nonexistent user.
        """
        resp = self.client.get('/api/v1/presence_weekday/0')
        self.assertEqual(resp.status_code, 404)

    def test_api_presence_weekday(self):
        """
        Test total presence time of given user grouped by weekday.
        """
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 8)
        self.assertEqual(
            data,
            [
                [u'Weekday', u'Presence (s)'],
                [u'Mon', 0],
                [u'Tue', 30047],
                [u'Wed', 24465],
                [u'Thu', 23705],
                [u'Fri', 0],
                [u'Sat', 0],
                [u'Sun', 0]
            ]
        )

    def test_api_presence_start_end_404(self):
        """
        Test timespans for nonexistent employee.
        """
        resp = self.client.get('/api/v1/presence_start_end/0')
        self.assertEqual(resp.status_code, 404)

    def test_api_presence_start_end(self):
        """
        Test timespans when the employee is most often present in the office.
        """
        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 5)
        self.assertItemsEqual(
            data,
            [
                {u'start': 0.0, u'end': 0.0},
                {u'start': 34745000.0, u'end': 64792000.0},
                {u'start': 33592000.0, u'end': 58057000.0},
                {u'start': 38926000.0, u'end': 62631000.0},
                {u'start': 0.0, u'end': 0.0}
            ]
        )


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_seconds_since_midnight(self):
        """
        Test calculating amount of seconds since midnight.
        """
        test_time = datetime.datetime.strptime('01:06:06', '%H:%M:%S').time()
        self.assertEqual(utils.seconds_since_midnight(test_time), 3966)

    def test_interval(self):
        """
        Test calculating inverval in seconds between two datetime.time objects.
        """
        start_time = datetime.datetime.strptime('01:06:00', '%H:%M:%S').time()
        end_time = datetime.datetime.strptime('01:07:06', '%H:%M:%S').time()
        self.assertEqual(utils.interval(start_time, end_time), 66)

    def test_mean(self):
        """
        Tests calculating arithmetic mean. Returns zero for empty lists.
        """
        self.assertEqual(utils.mean([1, 2, 3, 3]), 2.25)
        self.assertEqual(utils.mean([]), 0.0)

    def test_group_by_weekday(self):
        """
        Test grouping presence entries by weekday.
        """
        sample_data = {
            datetime.date(2015, 4, 7): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2015, 4, 8): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(9, 0, 0),
            },
        }
        grouping = utils.group_by_weekday(sample_data)
        self.assertEqual(grouping, [[], [30600], [1800], [], [], [], []])

    def test_get_mean_by_weekday(self):
        """
        Test grouping mean seconds since midnight
        (either start or end) by weekday.
        """
        sample_data = {
            datetime.date(2015, 4, 7): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2015, 4, 8): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(9, 0, 0),
            },
        }
        res = utils.get_mean_by_weekday(sample_data, 'start')
        self.assertEqual(res, [0, 32400.0, 30600.0, 0, 0, 0, 0])
        res = utils.get_mean_by_weekday(sample_data, 'end')
        self.assertEqual(res, [0, 63000.0, 32400.0, 0, 0, 0, 0])


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
