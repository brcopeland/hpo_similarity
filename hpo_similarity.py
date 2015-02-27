""" assess similarity of HPO terms in sets of probands.

If we have a set of probands who we know share some genetic feature in a gene,
we would like to know what is the probability of them sharing sharing their
Human Phenotype Ontology (HPO; standardised phenotypes) terms.

The HPO terms form a graph, so in order to estimate similarity, we use common
ancestors of sets of terms.
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import argparse
import bisect
import math
import random

from src.load_files import load_participants_hpo_terms, load_variants
from src.hpo_ontology import Ontology
from src.shared_term_plots import plot_shared_terms
from src.similarity import ICSimilarity

HPO_PATH = os.path.join(os.path.dirname(__file__), "data", "hp.obo")
DATAFREEZE_DIR = "/nfs/ddd0/Data/datafreeze/ddd_data_releases/2014-11-04/"
PHENOTYPES_PATH = os.path.join(DATAFREEZE_DIR, "phenotypes_and_patient_info.txt")
ALTERNATE_IDS_PATH = os.path.join(DATAFREEZE_DIR, "person_sanger_decipher.txt")

def get_options():
    """ get the command line switches
    """
    
    parser = argparse.ArgumentParser(description="Examines the likelihood of \
        obtaining similar HPO terms in probands with variants in the same gene.")
    parser.add_argument("--variants", dest="variants_path", required=True, \
        default="/nfs/users/nfs_j/jm33/apps/mupit/data-raw/de_novo_datasets/ \
            de_novos.ddd_4k.ddd_only.txt", \
        help="Path to file listing known variants in genes. See example file \
            in data folder for format.")
    parser.add_argument("--output", required=True, help="path to output file")
    
    args = parser.parse_args()
    
    return args

def geomean(values):
    """ calculate the geometric mean of a list of floats.
    
    Args:
        values: list of values, none of which are zero or less. The function
            will raise an error if the list is empty.
    
    Returns:
        The geometric mean as float.
    """
    
    values = [math.log10(x) for x in values]
    mean = sum(values)/float(len(values))
    
    return 10**mean

def get_score_for_pair(matcher, proband_1, proband_2):
    """ Calculate the similarity in HPO terms between terms for two probands.
    
    Currently we use the geometric mean of the
    
    Args:
        matcher: PathLengthSimilarity object for the HPO term graph, with
            information on how many times each term has been used across all
            probands.
        proband_1: list of HPO terms for one proband
        proband_2: list of HPO terms for the other proband
    
    Returns:
        A score for how similar the terms are between the two probands.
    """
    
    ic = []
    for term_1 in proband_1:
        for term_2 in proband_2:
            ic.append(matcher.get_max_ic(term_1, term_2))
    
    return geomean(ic)
    
def get_proband_similarity(matcher, hpo_terms):
    """ calculate the similarity of HPO terms across different individuals.
    
    We start with a list of HPO lists e.g. [[HP:01, HP:02], [HP:02, HP:03]],
    and calculate a matrix of similarity scores for each pair of probands in the
    HPO lists. We condense that to a single score that estimates the similarity
    across all the probands.
    
    Args:
        matcher: PathLengthSimilarity object for the HPO term graph, with
            information on how many times each term has been used across all
            probands.
        hpo_terms: List of HPO terms found for each proband with variants for
            the current gene e.g. [[HP:01, HP:02], [HP:02, HP:03]].
    
    Returns:
        The summed similarity score across the HPO terms for each proband.
    """
    
    ic_scores = []
    for pos in range(len(hpo_terms)):
        proband = hpo_terms[pos]
        
        # remove the proband, so we don't match to itself
        others = hpo_terms[:]
        others.pop(pos)
        
        for other in others:
            # for each term in the proband, measure how well it matches the
            # terms in another proband
            score = get_score_for_pair(matcher, proband, other)
            ic_scores.append(score)
    
    return sum(ic_scores)

def test_similarity(matcher, family_hpo, probands, n_sims=1000):
    """ find if groups of probands per gene share HPO terms more than by chance.
    
    Args:
        matcher: PathLengthSimilarity object for the HPO term graph, with
            information on how many times each term has been used across all
            probands.
        family_hpo: list of FamilyHPO objects for all probands.
        probands: list of proband IDs.
    
    Returns:
        The probability that the HPO terms used in the probands match as well as
        they do.
    """
    
    hpo_terms = [family_hpo[x].get_child_hpo() for x in probands if x in family_hpo]
    other_probands = [x for x in family_hpo if x not in probands]
    
    # We can't test similarity from a single proband. We don't call this
    # function for genes with a single proband, however, sometimes only one of
    # the probands has HPO terms recorded. We cannot estimate the phenotypic
    # similarity between probands in this case, so return None instead.
    if len(hpo_terms) == 1:
        return None
    
    observed = get_proband_similarity(matcher, hpo_terms)
    
    # get a distribution of scores for randomly sampled HPO terms
    distribution = []
    for x in range(n_sims):
        sampled = random.sample(other_probands, len(probands))
        simulated = [family_hpo[n].get_child_hpo() for n in sampled]
        predicted = get_proband_similarity(matcher, simulated)
        distribution.append(predicted)
    distribution = sorted(distribution)
    
    # figure out where in the distribution the observed value occurs
    pos = bisect.bisect_left(distribution, observed)
    sim_prob = (abs(pos - len(distribution)))/(1 + len(distribution))
    
    return sim_prob

def analyse_genes(matcher, family_hpo, probands_by_gene, output_path):
    """ tests genes to see if their probands share HPO terms more than by chance.
    
    Args:
        matcher: PathLengthSimilarity object for the HPO term graph, with
            information on how many times each term has been used across all
            probands.
        family_hpo: list of FamilyHPO objects for all probands
        probands_by_gene: dictionary of genes, to the probands who have variants
            in those genes.
        output_path: path to file to write the results to.
    """
    
    output = open(output_path, "w")
    output.write("hgnc\thpo_similarity_p_value\n")
    
    for gene in sorted(probands_by_gene):
        probands = probands_by_gene[gene]
        
        p_value = "NA"
        if len(probands) > 1:
            p_value = test_similarity(matcher, family_hpo, probands)
        
        if p_value is None:
            p_value = "NA"
        
        if p_value == "NA":
            continue
        
        output.write("{0}\t{1}\n".format(gene, p_value))
    
    output.close()

def main():
    
    options = get_options()
    
    # build a graph of DDG2P terms, so we can trace paths between terms
    hpo_ontology = Ontology(HPO_PATH)
    hpo_graph = hpo_ontology.get_graph()
    alt_node_ids = hpo_ontology.get_alt_ids()
    obsolete_ids = hpo_ontology.get_obsolete_ids()
    
    # load HPO terms and probands for each gene
    print("loading HPO terms and probands by gene")
    family_hpo_terms = load_participants_hpo_terms(PHENOTYPES_PATH, ALTERNATE_IDS_PATH, alt_node_ids, obsolete_ids)
    probands_by_gene = load_variants(options.variants_path)
    
    matcher = ICSimilarity(family_hpo_terms, hpo_graph, alt_node_ids)
    matcher.tally_hpo_terms(family_hpo_terms, source="child_hpo")
    
    print("analysing similarity")
    analyse_genes(matcher, family_hpo_terms, probands_by_gene, options.output)

if __name__ == '__main__':
    main()
