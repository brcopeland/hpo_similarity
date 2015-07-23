"""
Copyright (c) 2015 Wellcome Trust Sanger Institute

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

def get_score_for_pair(hpo_graph, proband_1, proband_2):
    """ Calculate the similarity in HPO terms between terms for two probands.
    
    This runs through the pairs of HPO terms from the two probands and finds
    the information content for the most informative common ancestor for each
    pair. We return the largest of these IC scores, known as the maxIC.
    
    Args:
        hpo_graph: ICSimilarity object for the HPO term graph, with
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
            ic.append(hpo_graph.get_most_informative_ic(term_1, term_2))
    
    return max(ic)
    
def get_proband_similarity(hpo_graph, probands):
    """ calculate the similarity of HPO terms across different individuals.
    
    We start with a list of HPO lists e.g. [[HP:01, HP:02], [HP:02, HP:03]],
    and calculate a matrix of similarity scores for each pair of probands in the
    HPO lists. We collapse that to a single score that estimates the similarity
    across all the probands.
    
    Args:
        hpo_graph: ICSimilarity object for the HPO term graph, with
            information on how many times each term has been used across all
            probands.
        probands: List of HPO terms found for each proband with variants for
            the current gene e.g. [[HP:01, HP:02], [HP:02, HP:03]].
    
    Returns:
        The summed similarity score across the HPO terms for each proband.
    """
    
    ic_scores = []
    for x in range(len(probands)):
        for y in range(x, len(probands)):
            # don't match a proband to itself
            if x == y:
                continue
            
            # for each term in the proband, measure how well it matches the
            # terms in another proband
            score = get_score_for_pair(hpo_graph, probands[x], probands[y])
            ic_scores.append(score)
    
    return sum(ic_scores)
