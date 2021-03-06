# coding=utf-8
import logging
import os
import shutil
import unittest

from realtime import settings
from realtime.earthquake.process_event import process_event
from realtime.earthquake.settings import EQ_GRID_ALGORITHM
from realtime.earthquake.shake_hazard import ShakeHazard
from realtime.settings import ON_TRAVIS
from realtime.tests.mock_server import InaSAFEDjangoMockServer, \
    InaSAFEDjangoMockServerHandler
from realtime.utilities import realtime_logger_name
from safe.test.qgis_app import qgis_app
from safe.utilities.keyword_io import KeywordIO

APP, IFACE = qgis_app()
LOGGER = logging.getLogger(realtime_logger_name())


class TestShakeHazard(unittest.TestCase):

    def fixture_path(self, *path):
        current_dir = os.path.dirname(__file__)
        return os.path.abspath(os.path.join(current_dir, 'fixtures', *path))

    def setUp(self):
        self.output_dir = self.fixture_path('../output')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # mock url
        self.inasafe_django_rest_url = settings.INASAFE_REALTIME_REST_URL
        self.mock_host = 'localhost'
        self.mock_port = 8000
        settings.INASAFE_REALTIME_REST_URL = (
            'http://{host}:{port}/realtime/api/v1').format(
            host=self.mock_host, port=self.mock_port)

        # # Configure Mock Server
        self.mock_server = InaSAFEDjangoMockServer(
            self.mock_host, self.mock_port, InaSAFEDjangoMockServerHandler)
        self.mock_server.start_server()

    def tearDown(self):
        if ON_TRAVIS:
            try:
                shutil.rmtree(self.output_dir)
            except BaseException:
                pass

        # restore url
        settings.INASAFE_REALTIME_REST_URL = self.inasafe_django_rest_url

        # shutdown mock server
        self.mock_server.shutdown()

    def test_grid_conversion(self):
        """Test Shake Grid conversion to InaSAFE Hazard Layer."""
        shake_hazard = ShakeHazard(
            grid_file=self.fixture_path('grid.xml'),
            force_flag=True,
            algorithm=EQ_GRID_ALGORITHM,
            output_dir=self.output_dir)

        self.assertTrue(shake_hazard.hazard_exists)

        expected_data = {
            'depth': 3.0,
            'event_id': u'20161214005704',
            'hazard_path': '/home/app/realtime/earthquake/tests/'
                           'output/hazard-use_ascii.tif',
            'latitude': 4.92,
            'longitude': 96.55,
            'magnitude': 3.5,
            'source': 'BMKG (Badan Meteorologi, Klimatologi, dan Geofisika) '
                      'Indonesia',
            'source_type': 'initial',
            'time_zone': 'Asia/Jakarta',
            'timestamp': '2016-12-14 00:57:04+07:07'
        }

        actual_data = {
            'depth': shake_hazard.depth,
            'event_id': shake_hazard.event_id,
            'hazard_path': shake_hazard.hazard_path,
            'latitude': shake_hazard.latitude,
            'longitude': shake_hazard.longitude,
            'magnitude': shake_hazard.magnitude,
            'source': shake_hazard.source,
            'source_type': shake_hazard.source_type,
            'time_zone': shake_hazard.time_zone,
            'timestamp': str(shake_hazard.timestamp)
        }

        self.assertDictEqual(expected_data, actual_data)

        self.assertTrue(shake_hazard.is_valid())

        expected_extra_keywords = {
            u'earthquake_event_id': u'20161214005704',
            u'earthquake_magnitude': 3.5,
            u'time_zone': u'Asia/Jakarta',
            u'earthquake_longitude': 96.55,
            u'earthquake_x_maximum': 97.8,
            u'earthquake_y_minimum': 3.675,
            u'earthquake_location': u'Aceh',
            u'earthquake_x_minimum': 95.3,
            u'earthquake_latitude': 4.92,
            u'earthquake_y_maximum': 6.165,
            u'earthquake_depth': 3.0,
            u'earthquake_event_time': u'2016-12-14T00:57:04'
        }

        keywords_io = KeywordIO()

        actual_extra_keywords = keywords_io.read_keywords(
            shake_hazard.hazard_layer, keyword='extra_keywords')

        self.assertDictEqual(expected_extra_keywords, actual_extra_keywords)

    def test_process_event(self):
        """Test process event executions."""
        ret_val = process_event(
            shake_id='20161214005704',
            grid_file=self.fixture_path('grid.xml'),
            output_dir=self.output_dir)

        self.assertTrue(ret_val)
