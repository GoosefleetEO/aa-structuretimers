from django.test import TestCase

from eveuniverse.tools.testdata import create_testdata, ModelSpec

from . import test_data_filename


class CreateEveUniverseTestData(TestCase):
    def test_create_testdata(self):
        testdata_spec = {
            "EveType": ModelSpec(ids=[35832, 35825, 35835], include_children=False,),
            "EveSolarSystem": ModelSpec(
                ids=[30004984, 30045339], include_children=False,
            ),
        }
        create_testdata(testdata_spec, test_data_filename())
