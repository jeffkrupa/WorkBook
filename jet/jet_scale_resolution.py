# Standard importts
import os,sys,socket,argparse
import os
import ROOT
import math
from array import array
ROOT.gROOT.SetBatch(True)

# RooFit
ROOT.gSystem.Load("libRooFit.so")
ROOT.gSystem.Load("libRooFitCore.so")
ROOT.gROOT.SetStyle("Plain")
ROOT.gSystem.SetIncludePath( "-I$ROOFITSYS/include/" )

from helper_functions import *

def main():
    
    parser = argparse.ArgumentParser(description='Plot resolution and response')
    parser.add_argument("-i", "--input"   ,dest="input"   , help="input file name", type=str)
    parser.add_argument("-o", "--output"  ,dest="output"  , help="output folder name", type=str)
    parser.add_argument("-e", "--eta"     ,dest="eta"     , help="define the eta range, examples are '0_1p3','1p3_2p1',2p1_2p5','2p5_3p0', '3p0_5p0'",type=str)
    parser.add_argument("-n", "--npv"     ,dest="npv"     , help="define the npv range, examples are '0_70','0_10','10_30','30_70'",type=str)
    args = parser.parse_args()    

    f_in = ROOT.TFile(str(args.input),"READ")
    t_in = f_in.Get("events")
    _pt  = [20,50,100,200,500,2000]
    _eta = [float(args.eta.split("_")[0].replace("p",".")), float(args.eta.split("_")[1].replace("p","."))]
    _npv = [float(args.npv.split("_")[0]), float(args.npv.split("_")[1])]

    folder = args.output+"/"
    os.system("mkdir -p "+folder)
    os.system("mkdir -p "+folder+"/fit")

    h_mean    = ROOT.TH1F("h_mean","h_mean",len(_pt)-1,array('d',_pt))
    h_sigma   = ROOT.TH1F("h_sigma","h_sigma",len(_pt)-1,array('d',_pt))
    h_sigma_corrected = ROOT.TH1F("h_sigma_corrected","h_sigma_corrected",len(_pt)-1,array('d',_pt))

    for i in range(0,len(_pt)-1):
        shape  = ROOT.TH1F("shape","shape",50,0.25,2.5)

        reco_bin = "jet_pt>10"
        gen_bin = "genjet_pt>"+str(_pt[i])+" && genjet_pt<"+str(_pt[i+1])
        eta_bin = "abs(genjet_eta)>="+str(_eta[0])+" && abs(genjet_eta)<"+str(_eta[1])
        npv_bin = "npv>="+str(_npv[0])+" && npv<"+str(_npv[1])
        t_in.Draw("rawjet_pt/genjet_pt>>shape",reco_bin + "&& " + gen_bin + "&&" + eta_bin + "&&" + npv_bin,"goff")

        mean, mean_error, sigma, sigma_error = ConvFit(shape ,False,"ratio","jet pt/gen jet pt",folder+"/fit","FIT_pt_"+str(_pt[i])+"_eta_"+args.eta+"_npv_"+args.npv)

        h_mean.SetBinContent(i+1,mean)
        h_mean.SetBinError(i+1,mean_error)

        #scale correct the resolution
        if mean>0:
            h_sigma_corrected.SetBinContent(i+1,sigma/mean)
        else:
            h_sigma_corrected.SetBinContent(i+1,0)

        h_sigma.SetBinContent(i+1,sigma)
        h_sigma.SetBinError(i+1,sigma_error)

        c = ROOT.TCanvas("mean","mean", 600, 600)
        c.cd()
        c.SetLogx()
        ROOT.gStyle.SetOptStat(False)
        h_mean.SetTitle("")
        h_mean.GetXaxis().SetTitle("Gen jet p_{T} [GeV]")
        h_mean.GetYaxis().SetTitle("Response")
        h_mean.GetXaxis().SetTitleOffset(1.2)
        h_mean.GetYaxis().SetTitleOffset(1.3)
        h_mean.SetMaximum(1.3)
        h_mean.SetMinimum(0.7)
        h_mean.SetLineWidth(2)
        h_mean.Draw("")
        h_mean.SetMarkerStyle(20)
        h_mean.SetMarkerSize(0.8)
        
        legend = ROOT.TLegend(0.30, 0.65, 0.65, .85);
        legend . AddEntry(h_mean,"chs jet" , "lp")

        legend.Draw("same")

        latex2 = ROOT.TLatex()
        latex2.SetNDC()
        latex2.SetTextSize(0.4*c.GetTopMargin())
        latex2.SetTextFont(42)
        latex2.SetTextAlign(31) # align right                                                     
        latex2.DrawLatex(0.90, 0.93,str(_eta[0])+" < #eta <"+ str(_eta[1]) + ", "+ str(_npv[0])+" < #npv < " + str(_npv[1]))

        latex2.Draw("same")

        c.SaveAs(folder+"FIT_mean_eta_"+args.eta+"_npv_"+args.npv+".png")
        c.SaveAs(folder+"FIT_mean_eta_"+args.eta+"_npv_"+args.npv+".pdf")

        c1 = ROOT.TCanvas("sigma","sigma", 600, 600)
        c1.cd()
        c1.SetLogx()
        h_sigma_corrected.GetXaxis().SetTitle("Gen jet p_{T} [GeV]")
        h_sigma_corrected.GetYaxis().SetTitle("Resolution / Response")
        h_sigma_corrected.SetTitle("")
        h_sigma_corrected.GetXaxis().SetTitleOffset(1.2)
        h_sigma_corrected.GetYaxis().SetTitleOffset(1.3)
        h_sigma_corrected.SetLineWidth(2)
        h_sigma_corrected.SetMaximum(0.5)
        h_sigma_corrected.SetMinimum(0)
        h_sigma_corrected.Draw()
        h_sigma_corrected.SetMarkerStyle(20)
        h_sigma_corrected.SetMarkerSize(0.8)

        latex2 = ROOT.TLatex()
        latex2.SetNDC()
        latex2.SetTextSize(0.4*c1.GetTopMargin())
        latex2.SetTextFont(42)
        latex2.SetTextAlign(31) # align right                                                     
        latex2.DrawLatex(0.90, 0.93,str(_eta[0])+" < #eta <"+ str(_eta[1]) + ", "+ str(_npv[0])+" < #pv < " + str(_npv[1]))

        latex2.Draw("same")

        legend.Draw("same")
        c1.SaveAs(folder+"FIT_sigma_eta_"+args.eta+"_npv_"+args.npv+".png")
        c1.SaveAs(folder+"FIT_sigma_eta_"+args.eta+"_npv_"+args.npv+".pdf")

        c2 = ROOT.TCanvas("sigmaabs","sigmaabs", 600, 600)
        c2.cd()
        c2.SetLogx()
        h_sigma.GetXaxis().SetTitle("Gen jet p_{T} [GeV]")        
        h_sigma.GetYaxis().SetTitle("Resolution")
        h_sigma.SetTitle("")
        h_sigma.GetXaxis().SetTitleOffset(1.2)
        h_sigma.GetYaxis().SetTitleOffset(1.3)
        h_sigma.SetLineWidth(2)
        h_sigma.SetMaximum(0.5)
        h_sigma.SetMinimum(0)
        h_sigma.SetMarkerStyle(20)
        h_sigma.SetMarkerSize(0.8)
        h_sigma.Draw("")

        latex2 = ROOT.TLatex()
        latex2.SetNDC()
        latex2.SetTextSize(0.4*c2.GetTopMargin())
        latex2.SetTextFont(42)
        latex2.SetTextAlign(31) # align right                                                     
        latex2.DrawLatex(0.90, 0.93,str(_eta[0])+" < #eta <"+ str(_eta[1]) + ", "+ str(_npv[0])+" < #pv < " + str(_npv[1]))

        latex2.Draw("same")

        legend.Draw("same")
        c2.SaveAs(folder+"FIT_sigmaabs_eta_"+args.eta+"_npv_"+args.npv+".png")
        c2.SaveAs(folder+"FIT_sigmaabs_eta_"+args.eta+"_npv_"+args.npv+".pdf")

if __name__ == '__main__':
    main()
