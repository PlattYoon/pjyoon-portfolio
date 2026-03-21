# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 17:32:48 2018

@author: jdkan
"""
import time
import alignment
import copy
import math
# Your task is to *accurately* predict the primer melting points using machine 
# learning based on the sequence of the primer.

# Load the primers and their melting points.

reverse_map = {'A':'T', 'T':'A', 'C':'G', 'G':'C',
               'a':'t', 't':'a', 'c':'g', 'g':'c', "N":'n', 'n':'N'}
def reverse_complement(s):
    return ''.join([reverse_map[c] for c in s[::-1]])

def primerLength(seq):
    return len(seq)

# GC content (percentage)
def primerGC(seq):
    length = len(seq)
    gcCount = 0
    for i in range(length):
        if seq[i] == 'C' or seq[i] == 'G':
            gcCount += 1
    return (gcCount/length) * 100

# longest repeat
def longestRepeat(seq):
    maxRepeat = 0
    length = len(seq)
    if length >= 2:
        for i in range(length - 1):
            currPair = seq[i:i+1]
            currRepeat = 1
            next = i + 2
            while next < length - 1 and seq[next:next + 1] == currPair:
                currRepeat += 1
                next = next + 2
            maxRepeat = max(currRepeat, maxRepeat)
    return maxRepeat

# longest run
def longestRun(seq):
    maxRun = 1
    currRun = 1
    for  i in range(len(seq) - 1):
        if seq[i] == seq[i + 1]:
            currRun += 1
        else:
            currRun = 1
        if currRun >= maxRun:
                maxRun = currRun
    return maxRun



def CalculatePrimerFeatures(seq):
    length = primerLength(seq)
    gc_content = primerGC(seq)
    longest_repeat = longestRepeat(seq)
    longest_run = longestRun(seq)
    features = [length, gc_content, longest_repeat, longest_run]
    return features

def PredictPCRProduct(primer1, primer2, template_sequence, melting_point_rf):
    """
    Input:
        primer1 = a primer sequence in 5' to 3' order
        primer2 = a primer sequence in 5' to 3' order
        template_sequence = sequence from which we are trying to generate 
        copies using PCR in 5' to 3' order.  Assume this is double stranded, 
        but we are only including the top strand in the argument.
        melting_point_rf = random forest learned from task1 to predict primer
        melting points.
    Output:
        return sequence of successful PCR amplication reaction or None (if 
        there is no successful reaction)
        
    """

    # need: 18-35 bases long
    # need: 60C +- 2 melting point
    # need: binding to upper and lower
    if len(primer1) < 18 or len(primer1) > 35:
        return None
    if len(primer2) < 18 or len(primer2) > 35:
        return None

    
    primer1mp = melting_point_rf.predict([CalculatePrimerFeatures(primer1)])
    primer2mp = melting_point_rf.predict([CalculatePrimerFeatures(primer2)])
    if primer1mp < 58.0 or primer1mp > 62.0:
        return None
    if primer2mp < 58.0 or primer2mp > 62.0:
        return None

    L = len(template_sequence)
    
    # try primer1 bind to forward, primer2 bind to backward
    # aka reverse_complement(primer1) aligns to forward
    # primer2 aligns to backward
    # their separation is < 1000, so abs(primer1match - (L - primer2match)) <= 1000
    rev_template = reverse_complement(template_sequence)

    for p1, p2 in [(primer1, primer2)]:

        alf1 = alignment.local_align(
            p1, 
            template_sequence,
            score = alignment.ScoreParam(10, -5, -7),
            print_output=False
        )
        alf2 = alignment.local_align(
            reverse_complement(p2),
            template_sequence,
            score = alignment.ScoreParam(10, -5, -7),
            print_output=False
        )
        # alf[0] is the score, alf[1][0] is the starting location in template_sequence

        # make sure they match
        if (alf1[0] / (10 * len(p1))) < 0.8:
            #print("score1 doesnt match")
            continue
        if (alf2[0] / (10 * len(p2))) < 0.8:
            #print("score2 doesnt match")
            continue
    
        primer1location = alf1[1][0] - 1
        primer2location = alf2[1][1]
        distupstream = primer2location - primer1location
        #print(primer1location, primer2location)

    
        if 0 > distupstream or distupstream > 1000:
            #print("distance not valid: ", distupstream)
            continue

        #print(template_sequence.find(p1), template_sequence.find(reverse_complement(p2)))

    
        return template_sequence[primer1location:primer2location]
    #print("reached end")
    return None

def Task4(seqs, task1model):
    resprimers = {}
    products = {}
    for whichseq in range(len(seqs)):
        curseq = seqs[whichseq]

        for i in range(0, len(curseq) - 18 - 1):
            badjs = set()
            found_specific = False

            for j in range(len(curseq) - 18 - 1, i + 18 + 1, -1):
                if j in badjs:
                    continue

                fprimer = curseq[i:i + 18]
                bprimer = curseq[j:j + 18]
                product = curseq[i:j + 18]
                if j + 18 - i > 1000:
                    continue
                
                mpfprimer = task1model.predict([CalculatePrimerFeatures(fprimer)])
                mpbprimer = task1model.predict([CalculatePrimerFeatures(bprimer)])

                if mpfprimer < 58.0 or mpfprimer > 62.0:
                    # forward primer is bad
                    break
                if mpbprimer < 58.0 or mpbprimer > 62.0:
                    badjs.add(j)
                    continue

                # ensure it DOES NOT align 
                res = True

                print("checking specificity")
                
                for otherseq in range(len(seqs)):
                    if otherseq == whichseq:
                        continue
                    
                    alignforward = alignment.local_align(
                        fprimer, 
                        seqs[otherseq],
                        score = alignment.ScoreParam(10, -5, -7),
                        print_output=False
                    )

                    alignbackward = alignment.local_align(
                        bprimer, 
                        seqs[otherseq],
                        score = alignment.ScoreParam(10, -5, -7),
                        print_output=False
                    )
                    score1 = alignforward[0] / (10 * len(fprimer))
                    score2 = alignbackward[0] / (10 * len(bprimer))
                    #print("score1: ", score1)
                    #print("score2: ", score2)
                    if score1 >= 0.8:
                        fprimerbad = True
                        res = False
                        break
                    if score2 >= 0.8:
                        res = False
                        badjs.add(j)
                        break

                    # check length
                    curlen = alignbackward[1][1] - (alignforward[1][1]  + 1 - 18)
                    if curlen > 1000:
                        res = False
                        break
                    print("found a primer for seq ", whichseq, " that does not align to ", otherseq)

                if res:
                   resprimers[whichseq] = (fprimer, reverse_complement(bprimer))
                   found_specific = True
                   products[whichseq] = product
                   break
            if found_specific:
                break

    print("reached end")
    return resprimers, products



    


def Task3(seqs, task1model):
    # for each sequence:
    # choose the sequence as the main sequence
    # for each possible forward and reverse primer location:
    #     check melting point
    #     run task2() on other two sequences

    # how to iterate through forward and reverse primer location:
    numgoodtemp = 0
    
    for whichseq in range(len(seqs)):
        print("on sequence: ", whichseq)
        curseq = seqs[whichseq]

        for pflen in range(18, 36):

            for i in range(0, len(curseq)- pflen - 1):
                print("testing fprimer: ", i, " pflen: ", pflen, " whichseq: ", whichseq, " numsofar: ", numgoodtemp)
                badjs = set()
                for j in range(len(curseq) - pflen - 1, i + pflen + 1, -1):
                    if j in badjs:
                        continue
                    fprimer = curseq[i:i + pflen]
                    bprimer = curseq[j:j + pflen]
                    indices = {whichseq: (i, j + pflen)}
                    products = {whichseq: curseq[i:j + pflen]}
                    if j + pflen - i > 1000:
                        continue

                    mpfprimer = task1model.predict([CalculatePrimerFeatures(fprimer)])
                    mpbprimer = task1model.predict([CalculatePrimerFeatures(bprimer)])

                    if mpfprimer < 58.0 or mpfprimer > 62.0:
                        # forward primer is bad
                        break
                    numgoodtemp += 1
                    if mpbprimer < 58.0 or mpbprimer > 62.0:
                        badjs.add(j)
                        continue

                    res = True
                    fprimerbad = False
                    


                    for otherseq in range(len(seqs)):
                        if otherseq == whichseq:
                            continue
                        alignforward = alignment.local_align(
                            fprimer, 
                            seqs[otherseq],
                            score = alignment.ScoreParam(10, -5, -7),
                            print_output=False
                        )

                        alignbackward = alignment.local_align(
                            bprimer, 
                            seqs[otherseq],
                            score = alignment.ScoreParam(10, -5, -7),
                            print_output=False
                        )
                        score1 = alignforward[0] / (10 * len(fprimer))
                        score2 = alignbackward[0] / (10 * len(bprimer))
                        #print("score1: ", score1)
                        #print("score2: ", score2)
                        if score1 < 0.8:
                            fprimerbad = True
                            res = False
                            break
                        if score2 < 0.8:
                            res = False
                            break

                        # check for length

                        indices[otherseq] = (alignforward[1][1] + 1 - len(fprimer), alignbackward[1][1])
                        curlen = indices[otherseq][1] - indices[otherseq][0]
                        if curlen > 1000:
                            res = False
                            break
                        products[otherseq] = seqs[otherseq][indices[otherseq][0]:indices[otherseq][1]]
                        #print("passed alignment: ", otherseq)




                    if fprimerbad: 
                        break
                    if res:
                        #print("found correctly aligned sequence")
                        #print(indices)
                        #if Task4(indices, seqs):
                        return fprimer, reverse_complement(bprimer), products

    return None            



                


                



def LoadFastA(path):
    infile = open(path, 'r')
    seq = ""
    infile.readline()
    for line in infile:
        seq += line[:-1]
    return seq
    
if __name__ == "__main__":
   # stuff only to run when not called via 'import' here
   from sklearn.metrics import r2_score
   from sklearn.ensemble import RandomForestRegressor
   import importlib
   import os
   import sys

   print("Running Task 1:")
   
   infile = open("training_primers.txt", 'r')
   infile.readline() # don't load headers
   primers = []
   melting_points = []
   features = []
   st = time.time()
   for line in infile:
       Line = line.split()
       primers.append(Line[0])
       melting_points.append(float(Line[1]))
       # calculate features
       features.append(CalculatePrimerFeatures(Line[0]))
   feat_time = (time.time()-st)/(len(features)/1000)
   # cross validation
   how_many_folds = 10 
   predictions = []
   truth = []
   my_len = len(features[-1])
    
   for fold in range(how_many_folds):
        #print ("Calculating Fold",fold)
        training_features = []
        training_outcomes = []
        testing_features = []
        testing_outcomes = []
        for c in range(len(melting_points)):
            if c % how_many_folds == fold:
                # put this one in testing data
                testing_features.append(features[c])
                testing_outcomes.append(melting_points[c])
            else:
                # put this one in training data
                training_features.append(features[c])
                training_outcomes.append(melting_points[c])
        # train the model
        
        rf = RandomForestRegressor(n_estimators = 200)
        rf.fit(training_features, training_outcomes)
        fold_predictions = rf.predict(testing_features)
        truth += testing_outcomes
        predictions += list(fold_predictions)
      
           
   #truth = np.array(truth)
   #predictions = np.array(predictions)        
   print("Task 1 Results:\n")
   print("R2 Score:", r2_score(truth, predictions))
   """
   Task 2:
   Design a function to predict whether a product will be made in a PCR reaction.
   Your function should take as input the template DNA and the two primers and 
   return the product or 'None'.

   This requires a local alignment function which is provided for you or you 
   can use another implementation.
    
   There are test cases in PCR_product_test_cases.txt.
   
   """
   task2_randomforest = RandomForestRegressor(n_estimators = 200)
   task2_randomforest.fit(features, melting_points)
   
   res1 = PredictPCRProduct("ACTG", "ACTG", 
                     "ACTCAGCGACTGC", task2_randomforest)

   #print("res1: ", res1)
   res2 = PredictPCRProduct(
       "TGGTGGGATGTCTTTCAACAGG",
       "AACTACGGAGAACTACAGCAACCT",
       "ACGTCAGCGAGCGCTACGACGTGGTGGGATGTCTTTCAACAGGACGGACTGACGCGACGACTGACTGTAGGCTAGGTTGCTGTAGTTCTCCGTAGTTAGCTACGACGCATGCAGCTGCA",
       task2_randomforest
   )
   #print("res2: ", res2)
   res3 = PredictPCRProduct(
       "TGGTGGGATGTCTTTCAACAGG",
       "AACTACGGAGAACTACAGCAACCT",
       "ACTGCATCAGCTACGACTGACGGCGACTACGGACGTATATCGACGATCTGCGCGTACTGGACGACTACGAGCAGCTACGACGACGGCA",
       task2_randomforest
   )
   #print("res3: ", res3)
   
   
   """
   Task 3:
   Design primers for a PCR reaction to distinguish between the three types 
   of DNA.  
   
   -Your primers should be between 18 and 35 bases long.  
   -They should have at least 80% match to the DNA strand.
   -Predicted melting points of any primers to be run in the same reaction
   should be between 58.0 and 62.0 C.
   -Products are distinguishable in length if their difference in length is >40
   bases
   -Your products should not be longer than 1000 bases.
   
   We are making predictions about the functionality of sets of primers.  We 
   will synthesize your group's primers and test them in the lab later.
     
   
   """
   print("Starting task 3")
   curseqs = ['Kangas10_A1_R2-16S-rRNA.fasta',
              'Kangas10_A2_R2-16S-rRNA.fasta',
              'Kangas10_A5_R2-16S-rRNA.fasta']
   

   curseqs = [LoadFastA('./bacteria_sequences/' + s).upper() for s in curseqs]

   res = Task3(curseqs, task2_randomforest)
   print(res)

   #res = Task4(curseqs, task2_randomforest)
   #print(res)
   
