# Standard importts
import os,sys,socket,argparse
import os
import ROOT
import math
from array import array
import numpy as np

ROOT.gROOT.SetBatch(True)

# RooFit
ROOT.gSystem.Load("libRooFit.so")
ROOT.gSystem.Load("libRooFitCore.so")
ROOT.gROOT.SetStyle("Plain") 
ROOT.gSystem.SetIncludePath( "-I$ROOFITSYS/include/" )

def ConvFit( ptbalance, pu, pli, jer, output, pt, eta, binning, isData=False):

    print "Performing a fit using convoluted templates and a pdf to get the mean and the width for the JER" 
    # declare the observable mean, and import the histogram to a RooDataHist

    tmp_sigma    = ptbalance.GetRMS()
    balance      = ROOT.RooRealVar("balance","p_{T}_{Jet}/p_{T}_{Z}",0.4, 1.3) ;
    variable_name = "p_{T}^{Z}"

    dh_ptbalance = ROOT.RooDataHist("dh_ptbalance"  ,"dh_ptbalance"  ,ROOT.RooArgList(balance),ROOT.RooFit.Import(ptbalance)) ;

    # plot the data hist with error from sum of weighted events
    frame        = balance.frame(ROOT.RooFit.Title("ptbalance"))
    if isData:
        dh_ptbalance.plotOn(frame,ROOT.RooFit.DataError(ROOT.RooAbsData.Poisson))
    else:
        dh_ptbalance.plotOn(frame,ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2)) ;
     
    # Now import the templates
    dh_pu  = ROOT.RooDataHist("dh_pu",  "dh_pu" , ROOT.RooArgList(balance),ROOT.RooFit.Import(pu)) ;
    dh_pli = ROOT.RooDataHist("dh_pli", "dh_pli", ROOT.RooArgList(balance),ROOT.RooFit.Import(pli)) ;
    dh_jer = ROOT.RooDataHist("dh_jer", "dh_jer", ROOT.RooArgList(balance),ROOT.RooFit.Import(jer)) ;
    
    pdf_pu  = ROOT.RooHistPdf("pdf_pu" , "pdf_pu" , ROOT.RooArgSet(balance), dh_pu);
    pdf_pli = ROOT.RooHistPdf("pdf_pli", "pdf_pli", ROOT.RooArgSet(balance), dh_pli);
    pdf_jer = ROOT.RooHistPdf("pdf_jer", "pdf_jer", ROOT.RooArgSet(balance), dh_jer);
    
    # create a simple gaussian pdf
    gauss_mean  = ROOT.RooRealVar("mean","mean",0,-1.0,1.0)
    gauss_sigma = ROOT.RooRealVar("sigma jer","sigma gauss",tmp_sigma,0,2.0)
    gauss       = ROOT.RooGaussian("gauss","gauss",balance,gauss_mean,gauss_sigma) 

    tmpxg = ROOT.RooFFTConvPdf("tmpxg","templates x gauss" ,balance,pdf_pli, gauss)

    #To let the fractions be calculated on the fly, need to convert them to extended pdfs
    nentries  = ptbalance.Integral()
    npu       = ROOT.RooRealVar("npu","npu",0,nentries)
    n         = ROOT.RooRealVar("n","n",0,nentries)

    extpdf_pu    = ROOT.RooExtendPdf("extpdf_pu"   , "extpdf_pu"   , pdf_pu   , npu)
    extpdf_tmpxg = ROOT.RooExtendPdf("extpdf_tmpxg", "extpdf_tmpxg", tmpxg, n)

    tmpfit = ROOT.RooAddPdf("tmpfit","tmpfit",ROOT.RooArgList(extpdf_pu,extpdf_tmpxg))

    tmpfit.fitTo(dh_ptbalance,ROOT.RooFit.Save(),ROOT.RooFit.SumW2Error(True))
    tmpfit.plotOn(frame)


    tmpfit.plotOn(frame, ROOT.RooFit.Components("extpdf_pu"),ROOT.RooFit.LineStyle(2),ROOT.RooFit.LineColor(8))
    tmpfit.plotOn(frame, ROOT.RooFit.Components("extpdf_tmpxg"),ROOT.RooFit.LineStyle(2),ROOT.RooFit.LineColor(2))

    argset_fit = ROOT.RooArgSet(gauss_mean,gauss_sigma)
    frame.SetMaximum(frame.GetMaximum()*1.25)

    # add chi2 info
    chi2_text = ROOT.TPaveText(0.15,0.72,0.15,0.88,"NBNDC")
    chi2_text.SetTextAlign(11)
    chi2_text.AddText("#chi^{2} fit = %s" %round(frame.chiSquare(6),2))
    chi2_text.AddText("#sigma_{gauss} "+"= {} #pm {}".format(round(gauss_sigma.getVal(),3), round(gauss_sigma.getError(),3)))
    chi2_text.AddText("#mu_{gauss} "+"= {} #pm {}".format(round(gauss_mean.getVal(),3), round(gauss_mean.getError(),3)) )
    chi2_text.SetTextSize(0.03)
    chi2_text.SetTextColor(2)
    chi2_text.SetShadowColor(0)
    chi2_text.SetFillColor(0)
    chi2_text.SetLineColor(0)
    frame.addObject(chi2_text)

    cfit = ROOT.TCanvas("cfit","cfit",600,600)
    frame.Draw()

    latex2 = ROOT.TLatex()
    latex2.SetNDC()
    latex2.SetTextSize(0.3*cfit.GetTopMargin())
    latex2.SetTextFont(42)
    latex2.SetTextAlign(31) # align right                                                     

    if isData:        
        latex2.DrawLatex(0.90, 0.93,pt.split("to")[0]+" GeV < "+variable_name+" < "+pt.split("to")[1]+" GeV, "+eta.split("to")[0].replace("p",".")+" < |#eta_{jet}| < "+eta.split("to")[1].replace("p",".")+ ", Data")
    else:
        latex2.DrawLatex(0.90, 0.93,pt.split("to")[0]+" GeV < "+variable_name+" < "+pt.split("to")[1]+" GeV, "+eta.split("to")[0].replace("p",".")+" < |#eta_{jet}| < "+eta.split("to")[1].replace("p",".")+ ", MC")
    latex2.Draw("same")

    frame.Print()
 
    legend = ROOT.TLegend(0.60,0.75,0.88,0.88)
    legend.AddEntry(frame.findObject("tmpfit_Norm[balance]_Comp[extpdf_pu]"),"pile up","l")
    legend.AddEntry(frame.findObject("tmpfit_Norm[balance]_Comp[extpdf_tmpxg]"),"pli #otimes gauss","l")
    legend.SetFillColor(0);
    legend.SetLineColor(0);
    legend.Draw("same")
 
    fit_filename = "fit_"+pt+"_"+eta
    if not os.path.exists(output): os.makedirs(output)
    if isData:
        cfit.SaveAs(os.path.join(output, fit_filename+"_Data.pdf"))
        cfit.SaveAs(os.path.join(output, fit_filename+"_Data.png"))
    else:
        cfit.SaveAs(os.path.join(output, fit_filename+".pdf"))
        cfit.SaveAs(os.path.join(output, fit_filename+".png"))
    del cfit

    return gauss_sigma.getVal(), gauss_sigma.getError(), gauss_mean.getVal(), gauss_mean.getError()

def main():

    parser = argparse.ArgumentParser(description='Extract resolution')
    parser.add_argument("-o", "--output", dest="output", help="output folder name", type=str)
    parser.add_argument("-b", "--binning",dest="binning",help="zpt or jetpt", type=str)
    args = parser.parse_args()    
    ROOT.gStyle.SetOptStat(0)

    inputfolder = "input/"
    data_filename = inputfolder+"DoubleMuon2018ALL_ptjet12.root"
    mc_filename = inputfolder+"MC2018ZtoMuMu_ptjet12.root"

    print "OPENING FILE", data_filename, "AND", mc_filename, args.binning
    f_data = ROOT.TFile(data_filename,"READ")
    f_mc   = ROOT.TFile(mc_filename,"READ")

    _eta   = ["0p000to0p783","0p783to1p305","1p305to1p930","1p930to2p500","2p500to2p964","2p964to3p200","3p200to5p191"]
    _pt    = ["30to40","40to50","50to60","60to85","85to105","105to130","130to175"]

    ### first define bining
    xbins = []
    ybins = []
    for ptBin in _pt:
        xbins.append(float(ptBin.split("to")[0]))                                
        xbins.append(float(ptBin.split("to")[1]))                                
    for etaBin in _eta:
        ybins.append(float(etaBin.split("to")[0].replace("p",".")))                
        ybins.append(float(etaBin.split("to")[1].replace("p",".")))                
    xbins.sort()
    ybins.sort()

    ## transform to numpy array for ROOT 
    xbinsT = np.array(xbins)
    ybinsT = np.array(ybins)
    ## just in case there are duplicates
    xbinsTab = np.unique(xbinsT)
    ybinsTab = np.unique(ybinsT)

    htitle = '#sigma_{jer}'
    hname  = 'jer'
    hdata = ROOT.TH2F(hname,htitle+" Data",xbinsTab.size-1,xbinsTab,ybinsTab.size-1,ybinsTab)
    hmc   = ROOT.TH2F(hname,htitle+" MC",xbinsTab.size-1,xbinsTab,ybinsTab.size-1,ybinsTab)
    hjec_data = ROOT.TH2F("hjec_data","#mu Data",xbinsTab.size-1,xbinsTab,ybinsTab.size-1,ybinsTab)
    hjec_mc   = ROOT.TH2F("hjec_mc","#mu MC",xbinsTab.size-1,xbinsTab,ybinsTab.size-1,ybinsTab)
    hresidual  = ROOT.TH2F("residual","residual (#mu_{data} - #mu_{mc})",xbinsTab.size-1,xbinsTab,ybinsTab.size-1,ybinsTab)
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetPaintTextFormat("4.3f")
    

    for i in range(0,len(_pt)):
        print _pt[i]
        for j in range(0,len(_eta)):

            folder            = args.binning+"_"+_pt[i].replace("to","_") 
            h_ptbal           = f_mc.Get(folder+"/h_PtRecoJetoverPtRecoZ_testsample_pt"+_pt[i]+"_eta"+_eta[j]+"_"+args.binning+"binning")
            h_ptbal_pu        = f_mc.Get(folder+"/h_PtRecoJetoverPtRecoZ_PU_pt"+_pt[i]+"_eta"+_eta[j]+"_"+args.binning+"binning")
            h_ptbal_matched   = f_mc.Get(folder+"/h_PtRecoJetoverPtRecoZ_GenMatchedJet_pt"+_pt[i]+"_eta"+_eta[j]+"_"+args.binning+"binning") 
            h_ptbal_unmatched = f_mc.Get(folder+"/h_PtRecoJetoverPtRecoZ_NoGenMatchedJet_pt"+_pt[i]+"_eta"+_eta[j]+"_"+args.binning+"binning")
            h_pli             = f_mc.Get(folder+"/h_PtGenJetoverPtGenZ_pt"+_pt[i]+"_eta"+_eta[j]+"_"+args.binning+"binning")
            h_jer             = f_mc.Get(folder+"/h_PtRecoJetoverPtGenJet_pt"+_pt[i]+"_eta"+_eta[j]+"_"+args.binning+"binning")
            h_ptbaldata       = f_data.Get(folder+"/h_PtRecoJetoverPtRecoZ_testsample_pt"+_pt[i]+"_eta"+_eta[j]+"_"+args.binning+"binning")
            h_ptbal_pudata    = f_data.Get(folder+"/h_PtRecoJetoverPtRecoZ_PU_pt"+_pt[i]+"_eta"+_eta[j]+"_"+args.binning+"binning")
            
            sigma, sigma_error, mean, mean_error = ConvFit(h_ptbal, h_ptbal_pu, h_pli, h_jer, args.output,_pt[i], _eta[j], args.binning)
            sigma_data, sigma_error_data, mean_data, mean_error_data = ConvFit(h_ptbaldata, h_ptbal_pudata, h_pli, h_jer, args.output,_pt[i], _eta[j], args.binning,isData=True)

            if sigma<0.001:
                print "Something went very WRONG! Taking RMS of the h_res"
                sigma = h_jer.GetRMS()
                sigma_error = h_jer.GetRMSError()
                    
            hmc.SetBinContent(i+1,j+1, round(float(sigma),4))
            hmc.SetBinError  (i+1,j+1, round(float(sigma_error),4))

            hdata.SetBinContent(i+1,j+1, round(float(sigma_data),4))
            hdata.SetBinError  (i+1,j+1, round(float(sigma_error_data),4))
    
            hjec_mc.SetBinContent(i+1,j+1, round(float(mean),4))
            hjec_mc.SetBinError(i+1,j+1, round(float(mean_error),4))

            hjec_data.SetBinContent(i+1,j+1, round(float(mean_data),4))
            hjec_data.SetBinError(i+1,j+1, round(float(mean_error_data),4))
            
            hresidual.SetBinContent(i+1,j+1, round(float(mean_data)-float(mean),4))
            hresidual.SetBinError(i+1,j+1, round(float(mean_error_data)-float(mean_error),4))

    if args.binning == "zpt":
        xname = "Z p_{T} [GeV]"
    else:
        xname = "Jet p_{T} [GeV]"

    hmc.GetYaxis().SetTitle("Jet #eta")    
    hmc.GetXaxis().SetTitle(xname)

    hdata.GetYaxis().SetTitle("Jet #eta")
    hdata.GetXaxis().SetTitle(xname)

    hresidual.GetYaxis().SetTitle("Jet #eta")
    hresidual.GetXaxis().SetTitle(xname)

    hjec_mc.GetYaxis().SetTitle("Jet #eta")
    hjec_mc.GetXaxis().SetTitle(xname)

    hjec_data.GetYaxis().SetTitle("Jet #eta")
    hjec_data.GetXaxis().SetTitle(xname)

    c2 = ROOT.TCanvas("c2","c2",600,600)
    hmc.Draw("colztext")

    if not os.path.exists(args.output): os.makedirs(args.output)
    c2.SaveAs(os.path.join(args.output, "h2_jer_mc"+".pdf"))
    c2.SaveAs(os.path.join(args.output, "h2_jer_mc"+".png"))

    c3 = ROOT.TCanvas("c3","c3",600,600)
    hdata.Draw("colztext")
    c3.SaveAs(os.path.join(args.output, "h2_jer_data"+".pdf"))
    c3.SaveAs(os.path.join(args.output, "h2_jer_data"+".png"))

    c4 = ROOT.TCanvas("c4","c4",600,600)
    hdata.Divide(hmc)
    hdata.SetNameTitle("jersf","#sigma_{jer} SF")
    hdata.Draw("colztext")
    c4.SaveAs(os.path.join(args.output, "h2_jer_sf"+".pdf"))
    c4.SaveAs(os.path.join(args.output, "h2_jer_sf"+".png"))

    c5 = ROOT.TCanvas("c5","c5",600,600)
    hresidual.Draw("colztext")
    c5.SaveAs(os.path.join(args.output, "h2_residual"+".pdf"))
    c5.SaveAs(os.path.join(args.output, "h2_residual"+".png"))

    c6 = ROOT.TCanvas("c6","c6",600,600)
    hjec_mc.Draw("colztext")
    c6.SaveAs(os.path.join(args.output, "h2_jec_mc"+".pdf"))
    c6.SaveAs(os.path.join(args.output, "h2_jec_mc"+".png"))

    c7 = ROOT.TCanvas("c7","c7",600,600)
    hjec_data.Draw("colztext")
    c7.SaveAs(os.path.join(args.output, "h2_jec_data"+".pdf"))
    c7.SaveAs(os.path.join(args.output, "h2_jec_data"+".png"))
        
    del c2, c3, c4, c5, c6, c7
    
if __name__ == '__main__':
    main()
