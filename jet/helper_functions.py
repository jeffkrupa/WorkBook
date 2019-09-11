# Standard importts
import os,sys,socket,argparse
import os
import ROOT
import math
from array import array
import numpy as n

ROOT.gROOT.SetBatch(True)

# RooFit
ROOT.gSystem.Load("libRooFit.so")
ROOT.gSystem.Load("libRooFitCore.so")
ROOT.gROOT.SetStyle("Plain")
ROOT.gSystem.SetIncludePath( "-I$ROOFITSYS/include/" )

def ConvFit( shape, isData, var_name, label, fit_plot_directory, fit_filename = None):

    print "Performing a fit using gaus x landau to get the mean and the width" 
    # declare the observable mean, and import the histogram to a RooDataHist

    tmp_mean = shape.GetMean()
    tmp_sigma = shape.GetRMS()

    tmp_mean_error = shape.GetMeanError()
    tmp_sigma_error = shape.GetRMSError()
    
    asymmetry   = ROOT.RooRealVar(var_name,label,0.5,1.5) ;
    dh          = ROOT.RooDataHist("datahistshape","datahistshape",ROOT.RooArgList(asymmetry),ROOT.RooFit.Import(shape)) ;
    
    # plot the data hist with error from sum of weighted events
    frame       = asymmetry.frame(ROOT.RooFit.Title(var_name))
    if isData:
        dh.plotOn(frame,ROOT.RooFit.DataError(ROOT.RooAbsData.Poisson))
    else:
        dh.plotOn(frame,ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2)) ;


    # create a simple gaussian pdf
    gauss_mean  = ROOT.RooRealVar("#mu_{gauss}","mean",0)
    gauss_sigma = ROOT.RooRealVar("#sigma_{gauss}","sigma gauss",tmp_sigma,0,2.0)
    gauss       = ROOT.RooGaussian("gauss","gauss",asymmetry,gauss_mean,gauss_sigma) 

    landau_mean  = ROOT.RooRealVar("#mu_{landau}","mean landau",1,0,2.0)
    landau_sigma = ROOT.RooRealVar("#sigma_{landau}","sigma landau",tmp_sigma,0,2.0)
    landau       = ROOT.RooLandau("landau","landau",asymmetry,landau_mean,landau_sigma)

    lxg = ROOT.RooFFTConvPdf("lxg","landau x gauss",asymmetry,landau,gauss)

    lxg.fitTo(dh,ROOT.RooFit.Save(),ROOT.RooFit.SumW2Error(True))

    lxg.plotOn(frame)

    argset_fit = ROOT.RooArgSet(gauss_mean,gauss_sigma)
    lxg.paramOn(frame,ROOT.RooFit.Format("NELU",ROOT.RooFit.AutoPrecision(1)),ROOT.RooFit.Layout(0.55)) 
    frame.SetMaximum(frame.GetMaximum()*1.2)

    # add chi2 info
    chi2_text = ROOT.TPaveText(0.3,0.8,0.4,0.9,"BRNDC")
    chi2_text.AddText("#chi^{2} fit = %s" %round(frame.chiSquare(6),2))
    chi2_text.SetTextSize(0.04)
    chi2_text.SetTextColor(2)
    chi2_text.SetShadowColor(0)
    chi2_text.SetFillColor(0)
    chi2_text.SetLineColor(0)
    frame.addObject(chi2_text)

    if fit_filename is not None:
        c = ROOT.TCanvas("cfit","cfit",600,700)
        frame.Draw()
        if not os.path.exists(fit_plot_directory): os.makedirs(fit_plot_directory)
        c.SaveAs(os.path.join( fit_plot_directory, fit_filename+".pdf"))
        c.SaveAs(os.path.join( fit_plot_directory, fit_filename+".png"))
        del c

    mean_asymmetry        = landau_mean.getVal()
    mean_asymmetry_error  = landau_mean.getError()

    rms_asymmetry        = gauss_sigma.getVal()
    rms_asymmetry_error  = gauss_sigma.getError()

    return mean_asymmetry, mean_asymmetry_error, rms_asymmetry, rms_asymmetry_error
