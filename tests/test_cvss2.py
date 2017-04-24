from os import path
import sys
import unittest

from cvss import CVSS2
from cvss.exceptions import CVSS2MalformedError, CVSS2MandatoryError, CVSS2RHScoreDoesNotMatch, \
    CVSS2RHMalformedError

WD = path.dirname(path.abspath(sys.argv[0]))  # Manage to run script anywhere in the path


class TestCVSS2(unittest.TestCase):
    def run_tests_from_file(self, test_name):
        with open(path.join(WD, test_name)) as f:
            for line in f:
                vector, expected_scores = line.split(' - ')
                expected_scores = expected_scores.replace('(', '').replace(')', '').strip().split(', ')
                expected_scores = tuple(float(a) if a != 'None' else None for a in expected_scores)
                result = CVSS2(vector)
                results_scores = result.scores()
                self.assertEqual(expected_scores, results_scores, test_name + ' - ' + vector)

    def run_rh_tests_from_file(self, test_name):
        with open(path.join(WD, test_name)) as f:
            for line in f:
                vector, expected_scores = line.split(' - ')
                expected_scores = expected_scores.replace('(', '').replace(')', '').strip().split(', ')
                expected_scores = tuple(float(a) if a != 'None' else None for a in expected_scores)
                tested_rh_vector = str(expected_scores[0]) + '/' + vector
                result = CVSS2.from_rh_vector(tested_rh_vector)
                results_scores = result.scores()
                self.assertEqual(expected_scores, results_scores, test_name + ' - ' + vector)

    def test_simple(self):
        """
        All vector combinations with only mandatory fields, 729 vectors.
        """
        self.run_tests_from_file('vectors_simple2')

    def test_calculator(self):
        """
        Hand picked vectors using https://nvd.nist.gov/CVSS-v2-Calculator . 3 vectors.

        Another 2 vectors added based on Issue #10, one of them does not match the calculator.
        """
        self.run_tests_from_file('vectors_calculator2')

    def test_cvsslib(self):
        """
        Tests which cvsslib from https://pypi.python.org/pypi/cvsslib uses. 24 vectors.
        """
        self.run_tests_from_file('vectors_cvsslib2')

    def test_random(self):
        """
        Random generated test vectors, values computed using cvsslib from
        https://pypi.python.org/pypi/cvsslib . 100,000 vectors.
        """
        self.run_tests_from_file('vectors_random2')

    def test_clean_vector(self):
        """
        Tests for cleaning-up vector, where fields are not in order or some fields have ND values.
        """
        v = 'AV:A/AC:L/Au:M/C:C/I:P/A:C/E:ND/CDP:ND/TD:M/IR:H/AR:H'
        self.assertEqual('AV:A/AC:L/Au:M/C:C/I:P/A:C/TD:M/IR:H/AR:H',
                         CVSS2(v).clean_vector())

        v = 'AV:A/AC:H/Au:S/C:C/I:C/A:P/E:U/RL:U/RC:UR/CDP:ND/TD:ND/CR:L/IR:M/AR:ND'
        self.assertEqual('AV:A/AC:H/Au:S/C:C/I:C/A:P/E:U/RL:U/RC:UR/CR:L/IR:M',
                         CVSS2(v).clean_vector())

        v = 'AV:A/AC:H/Au:M/C:C/I:N/A:C/CR:ND/IR:L/RL:W/RC:ND/CDP:H/E:POC/TD:N/AR:M'
        self.assertEqual('AV:A/AC:H/Au:M/C:C/I:N/A:C/E:POC/RL:W/CDP:H/TD:N/IR:L/AR:M',
                         CVSS2(v).clean_vector())

    def test_exceptions(self):
        """
        Test for exceptions in CVSS vector parsing.
        """
        v = ''
        self.assertRaises(CVSS2MalformedError, CVSS2, v)

        v = '/'
        self.assertRaises(CVSS2MalformedError, CVSS2, v)

        # Missing ':'
        v = 'AV:A/AC:L/Au:M/C:C/I:P/A:C/TD:M/IR:H/ARH'
        self.assertRaises(CVSS2MalformedError, CVSS2, v)

        # Unknown metric
        v = 'AX:A/AC:L/Au:M/C:C/I:P/A:C/TD:M/IR:H/AR:H'
        self.assertRaises(CVSS2MalformedError, CVSS2, v)

        # Unknown value
        v = 'AV:W/AC:L/Au:M/C:C/I:P/A:C/TD:M/IR:H/AR:H'
        self.assertRaises(CVSS2MalformedError, CVSS2, v)

        # Duplicate metric
        v = 'AV:A/AV:A/AC:L/Au:M/C:C/I:P/A:C/TD:M/IR:H/AR:H'
        self.assertRaises(CVSS2MalformedError, CVSS2, v)

        # Duplicate metric
        v = 'AV:A/AV:L/AC:L/Au:M/C:C/I:P/A:C/TD:M/IR:H/AR:H'
        self.assertRaises(CVSS2MalformedError, CVSS2, v)

        # Missing mandatory
        v = 'AV:L/AC:L/Au:M/C:C/I:P/TD:M/IR:H/AR:H'
        self.assertRaises(CVSS2MandatoryError, CVSS2, v)

    def test_rh_vector(self):
        """
        Test for parsing Red Hat style of CVSS vectors, e.g. containing score.
        """
        self.run_rh_tests_from_file('vectors_simple2')

        # Bad values
        v = '3.8/AV:L/AC:H/Au:M/C:C/I:N/A:N'
        self.assertRaises(CVSS2RHScoreDoesNotMatch, CVSS2.from_rh_vector, v)

        v = '6.0/AV:N/AC:L/Au:M/C:N/I:N/A:C'
        self.assertRaises(CVSS2RHScoreDoesNotMatch, CVSS2.from_rh_vector, v)

        v = '5.0/AV:L/AC:H/Au:M/C:C/I:P/A:P'
        self.assertRaises(CVSS2RHScoreDoesNotMatch, CVSS2.from_rh_vector, v)

        # Vector cannot be split to score/vector
        v = ''
        self.assertRaises(CVSS2RHMalformedError, CVSS2.from_rh_vector, v)

        v = '5.0|AV:L|AC:H|Au:M|C:C|I:P|A:P'
        self.assertRaises(CVSS2RHMalformedError, CVSS2.from_rh_vector, v)

        # Score is not float
        v = 'ABC/AV:L/AC:H/Au:M/C:C/I:P/A:P'
        self.assertRaises(CVSS2RHMalformedError, CVSS2.from_rh_vector, v)

if __name__ == '__main__':
    unittest.main()
