#!/usr/bin/env python
#=============================================================================#
#                                                                             #
# NAME:     fit_1D_poly_multinest.py                                          #
#                                                                             #
# PURPOSE:  Example of using PyMultiNest to fit a polynomial to some data     #
#                                                                             #
# MODIFIED: 24-Jan-2018 by C. Purcell                                         #
#                                                                             #
#=============================================================================#

# Input dataset 
specDat = "lineSpec.dat"

# Output directory for chains
outDir = "chains"

# Prior bounds for m and c in linear model y = m*x + c
boundsLst = [[  0.0,   1.0],    # 0 < m < 1 
             [-10.0, 100.0]]    # 0 < c < 100

# Prior type for each variable:
# "uniform" (default), "normal", "log" or "fixed" (=set to boundsLst[n][0])
priorType = ["uniform",
             "uniform"]

# Number of points
nPoints = 100

# Control verbosity
verbose = True


#=============================================================================#
import os
import sys
import shutil
import json
import numpy as np
import matplotlib as mpl
import pylab as pl
from scipy.special import ndtri

import pymultinest as pmn
from Imports import corner


#-----------------------------------------------------------------------------#
def main():
    
    # Read in the spectrum
    specArr = np.loadtxt(specDat, dtype="float64", unpack=True)
    xArr = specArr[0]
    yArr = specArr[1]
    dyArr = specArr[2]

    # Create the output directory
    if os.path.exists(outDir):
        shutil.rmtree(outDir, True)
    os.mkdir(outDir)

    # Set the prior function given the bounds of each parameter
    prior = prior_call(boundsLst, priorType)
    nDim = len(boundsLst)

    # DEBUG
    if False:
        print("\nPrior tranform range:")
        print("top:   %s" % prior([1., 1.], nDim, nDim))
        print("bottom %s" % prior([0., 0.], nDim, nDim))
        
    # Set the likelihood function
    lnlike = lnlike_call(xArr, yArr, dyArr)

    # DEBUG
    if False:
        print("\nlnlike output: %s " % lnlike([0.5, 10.10], nDim, nDim))
    
    # Run nested sampling
    pmn.run(lnlike,
            prior,
            nDim,
            outputfiles_basename = outDir + "/",
            n_live_points        = nPoints,
            verbose              = verbose)
    json.dump(['m', 'b'], open(outDir + '/params.json', 'w'))
    # Query the analyser object for results
    aObj = pmn.Analyzer(n_params = nDim, outputfiles_basename=outDir + "/")

    
#    print "\n", "-"*80
#    print "STATS"    
    statDict =  aObj.get_stats()
#    for k, v in statDict.iteritems():
#        print "\n", k,"\n", v

#    print "\n", "-"*80
#    print "BEST FIT"    
    fitDict =  aObj.get_best_fit()
    for k, v in fitDict.iteritems():
        print "\n", k,"\n", v

    # Get the best fitting values and uncertainties
    p = fitDict["parameters"]
    med = [None] *nDim
    dp = [[None, None]]*nDim
    for i in range(nDim):   
        dp[i] = statDict["marginals"][i]['1sigma']
        dp[i] = statDict["marginals"][i]['1sigma']
        med[i] = statDict["marginals"][i]['median']
        
    # Plot the data and best fit
    plot_model(p, xArr, yArr, dyArr)

    # Plot the triangle plot
    #pmn.plot.PlotMarginal(aObj)
    chains =  aObj.get_equal_weighted_posterior()
    print chains[:,:nDim].shape
    print chains[:,-1].shape
    
    #fig = corner.corner(chains[:,:nDim],
    #                    weights = chains[:,-1],
    #                    labels  = ['m', 'b'],
    #                    #range   = [0.99999]*nDim,
    #                    truths  = p)
    
    raw_input()
    
        
#-----------------------------------------------------------------------------#
def model(p, x):
    """ Evaluate the model given an X array """
    
    return p[0]*x + p[1]


#-----------------------------------------------------------------------------#
def lnlike_call(xArr, yArr, dyArr):
    """ Returns a function to evaluate the log-likelihood """

    def lnlike(p, nDim, nParams):
        return -0.5 * (np.sum( (yArr-model(p, xArr))**2./dyArr**2. ))

    return lnlike


#-----------------------------------------------------------------------------#
def prior_call(boundsLst, priorType):
    """Returns a function to transform (0-1) range to the distribution of 
    values for each parameter. Note that a numpy vectorised version of this
    function fails because of type-errors."""

    def rfunc(p, nDim, nParams):
	for i in range(nDim):
            if priorType[i] == "log":
		bMin = np.log(np.abs(boundsLst[i][0]))
		bMax = np.log(np.abs(boundsLst[i][1]))	
		p[i] *= bMax - bMin
		p[i] += bMin
		p[i] = np.exp(p[i])
            elif priorType[i] == "normal":
                bMin, bMax = boundsLst[i]
                sigma = (bMax - bMin)/2.0
                mu = bMin + sigma
                p[i] = mu + sigma * ndtri(p[i])
            elif priorType[i] == "fixed":
		p[i] = boundsLst[i][0]
            else: # uniform (linear)
                bMin, bMax = boundsLst[i]
                p[i] = bMin + p[i] * (bMax - bMin)
        return p
    
    return rfunc


#-----------------------------------------------------------------------------#
def plot_model(p, x, y, dy, scaleX=1.0):

    # Make the model curve
    nSamples = 100
    dXSamp = (np.max(x) - np.min(x)) / nSamples
    iLst = np.arange(nSamples, dtype='float32')
    xSamp = np.min(x) + dXSamp * iLst
    ySamp = model(p, xSamp)

    # Plot the channels and fit
    fig = pl.figure()
    fig.set_size_inches([8,4])
    ax = fig.add_subplot(1,1,1)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.plot(xSamp*scaleX, ySamp, color='b',marker='None',mfc='w',
            mec='g', ms=10, label='none', lw=1.0)
    ax.errorbar(x=x*scaleX , y=y, yerr=dy, mfc='none', ms=4, fmt='D',
                ecolor='red', elinewidth=1.0, capsize=2)
    fig.show()

    
#-----------------------------------------------------------------------------#
if __name__ == "__main__":
    main()