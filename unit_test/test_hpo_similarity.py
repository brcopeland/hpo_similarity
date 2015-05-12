""" class to test functions in hpo_similarity.py
"""

import os
import unittest

from src.ontology import Ontology
from src.similarity import ICSimilarity
from hpo_similarity import get_score_for_pair, get_proband_similarity, \
    test_similarity

class TestHpoSimilarityPy(unittest.TestCase):
    """ class to test hpo similarity fucntions
    """
    
    def setUp(self):
        """ construct a ICSimilarity object and terms per proband for unit tests
        """
        
        path = os.path.join(os.path.dirname(__file__), "data", "obo.txt")
        ontology = Ontology(path)
        graph = ontology.get_graph()
        
        self.hpo_terms = {
            "person_01": ["HP:0000924"],
            "person_02": ["HP:0000118", "HP:0002011"],
            "person_03": ["HP:0000707", "HP:0002011"]
        }
        
        self.hpo_graph = ICSimilarity(self.hpo_terms, graph)
    
    def test_get_score_for_pair(self):
        """ check that get_score_per_pair works correctly
        """
        
        # define the HPO terms per proband
        p1 = self.hpo_terms["person_01"]
        p2 = self.hpo_terms["person_02"]
        p3 = self.hpo_terms["person_03"]
        
        # check the max IC between different probands
        self.assertEqual(get_score_for_pair(self.hpo_graph, p1, p2), 0)
        self.assertEqual(get_score_for_pair(self.hpo_graph, p1, p3), 0)
        self.assertEqual(get_score_for_pair(self.hpo_graph, p2, p3), 0.916290731874155)
    
    def test_get_proband_similarity(self):
        """ check that get_proband_similarity works correctly
        """
        
        # check the default probands
        probands = list(self.hpo_terms.values())
        self.assertEqual(get_proband_similarity(self.hpo_graph, probands), 0.916290731874155)
        
        # add another proband, who has a rare term that matches a term in
        # another proband
        probands.append(["HP:0000924", "HP:0000118"])
        self.assertEqual(get_proband_similarity(self.hpo_graph, probands), 2.525728644308255)
    
    def test_test_similarity(self):
        """ check that test_similarity works correctly
        """
        
        # select two probands with relatively rare terms. Ignore that we select
        # the same person twice, the example will still work. Since the
        # reference population only has three individuals, the chance of
        # selecting two individuals with HPO similarity as rare as those two
        # individuals is 1 in three. We check that the probability estimate for
        # the two "rare" individuals is relatively close to 0.33.
        probands = ["person_03", "person_03"]
        p = test_similarity(self.hpo_graph, self.hpo_terms, probands, n_sims=1000)
        self.assertLess(abs(p - 0.33), 0.04)
        
        # now chose two individuals who do not share terms, and so the chance
        # that two random probands share their terms to the same extent is
        # effectively 1. The test is currently set up so that the maximum P-value
        # is actually n/(n + 1), where n is the number of iterations. We use
        # n + 1, since the observed similarity should be in the simulated
        # distribution under the null hypothesis.
        probands = ["person_01", "person_03"]
        p = test_similarity(self.hpo_graph, self.hpo_terms, probands, n_sims=1000)
        self.assertLess(abs(p - 0.999), 0.03)
        
