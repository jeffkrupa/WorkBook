# import ROOT in batch mode
import sys, os
import time
from array import array
from math import hypot, pi, sqrt, fabs
import ROOT

oldargv = sys.argv[:]
sys.argv = [ '-b-' ]
ROOT.gROOT.SetBatch(True)
sys.argv = oldargv

from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing('python')

#default options
options.inputFiles="/uscms_data/d3/zdemirag/JUMPSHOT/CMSSW_10_2_5/src/WorkBook/puppi/input/ReminiAOD.root"
options.outputFile="jetmetNtuples.root"
options.maxEvents=-1

#overwrite if given any command line arguments
options.parseArguments()
#in case of txt input file, read the information from txt
li_f=[]
for iF,F in enumerate(options.inputFiles):
	print F
	if F.split('.')[-1] == "txt":
		options.inputFiles.pop(iF)
		with open(F) as f:
			li_f+=f.read().splitlines()
options.inputFiles=li_f
print "analyzing files:"
for F in options.inputFiles: print F

# define deltaR
from math import hypot, pi, sqrt, fabs
import numpy as n

#from functions import *

# load FWLite C++ libraries
ROOT.gSystem.Load("libFWCoreFWLite.so");
ROOT.gSystem.Load("libDataFormatsFWLite.so");
ROOT.FWLiteEnabler.enable()

# load FWlite python libraries
from DataFormats.FWLite import Handle, Events

jets, jetLabel	    = Handle("std::vector<pat::Jet>"), "slimmedJets"
pjets, pjetLabel    = Handle("std::vector<pat::Jet>"), "slimmedJetsPuppi"
njets, njetLabel    = Handle("std::vector<pat::Jet>"), "patJetsPuppi"
vertex, vertexLabel = Handle("std::vector<reco::Vertex>"),"offlineSlimmedPrimaryVertices"

genjets, genjetLabel      = Handle("std::vector<reco::GenJet>"), "slimmedGenJets"

##Helper functions
#in order to print out the progress
def print_same_line(s):
	sys.stdout.write(s)					 # just print
	sys.stdout.flush()					  # needed for flush when using \x08
	sys.stdout.write((b'\x08' * len(s)).decode())# back n chars		

def deltaPhi(a,b):
    dphi = abs(float(a.phi()) - float(b.phi()))
    if (dphi <= pi): return dphi
    else: return 2*pi - dphi
        

def deltaR(a,b):
    dphi = deltaPhi(a,b)
    return hypot((a.eta()-b.eta()),dphi)


events = Events(options)
nevents = int(events.size())
print "total events: ", events.size()

outfile=ROOT.TFile("hists.root","recreate")

ROOT.TH1.SetDefaultSumw2()

#Init histograms
_npv = n.arange(0,70,7)
eff_npv = [] #efficiency
eff_npv.append(ROOT.TEfficiency("eff_npv_CHS","CHS",len(_npv)-1,array('d',_npv)))
eff_npv.append(ROOT.TEfficiency("eff_npv_PUPPI","PUPPI",len(_npv)-1,array('d',_npv)))
eff_npv.append(ROOT.TEfficiency("eff_npv_PUPPI","new PUPPI",len(_npv)-1,array('d',_npv)))

prt_npv = [] #Purity
prt_npv.append(ROOT.TEfficiency("prt_npv_CHS","CHS",len(_npv)-1,array('d',_npv)))
prt_npv.append(ROOT.TEfficiency("prt_npv_PUPPI","PUPPI",len(_npv)-1,array('d',_npv)))
prt_npv.append(ROOT.TEfficiency("prt_npv_newPUPPI","new PUPPI",len(_npv)-1,array('d',_npv)))

#for purity
h_chsjet_npv              = ROOT.TH1F("recojets_npv_CHS","CHS",len(_npv)-1,array('d',_npv))
h_chsjet_matched_npv      = ROOT.TH1F("matchedrecojets_npv_CHS","CHS",len(_npv)-1,array('d',_npv))
h_puppijet_npv            = ROOT.TH1F("recojets_npv_PUPPI","PUPPI",len(_npv)-1,array('d',_npv))
h_puppijet_matched_npv    = ROOT.TH1F("matchedrecojets_npv_PUPPI","PUPPI",len(_npv)-1,array('d',_npv))
h_newpuppijet_npv         = ROOT.TH1F("recojets_npv_newPUPPI","new PUPPI",len(_npv)-1,array('d',_npv))
h_newpuppijet_matched_npv = ROOT.TH1F("matchedrecojets_npv_newPUPPI","new PUPPI",len(_npv)-1,array('d',_npv))

#for efficiency
h_gen_chsjet_npv              = ROOT.TH1F("genjets_npv_CHS","CHS",len(_npv)-1,array('d',_npv))
h_gen_chsjet_matched_npv      = ROOT.TH1F("matchedgenjets_npv_CHS","CHS",len(_npv)-1,array('d',_npv))
h_gen_puppijet_npv            = ROOT.TH1F("genjets_npv_PUPPI","PUPPI",len(_npv)-1,array('d',_npv))
h_gen_puppijet_matched_npv    = ROOT.TH1F("matchedgenjets_npv_PUPPI","PUPPI",len(_npv)-1,array('d',_npv))
h_gen_newpuppijet_npv         = ROOT.TH1F("genjets_npv_newPUPPI","new PUPPI",len(_npv)-1,array('d',_npv))
h_gen_newpuppijet_matched_npv = ROOT.TH1F("matchedgenjets_npv_newPUPPI","new PUPPI",len(_npv)-1,array('d',_npv))

maxjet=1000

for ievent,event in enumerate(events):

	if options.maxEvents is not -1:
		if ievent > options.maxEvents: continue
	
	event.getByLabel(jetLabel, jets)
	event.getByLabel(pjetLabel, pjets)
	event.getByLabel(njetLabel, njets)
        event.getByLabel(genjetLabel, genjets)

	event.getByLabel(vertexLabel, vertex)

	print_same_line(str(round(100.*ievent/nevents,2))+'%')

	###CHS JETS
	matched_gen_jets=[]
	matched_rec_jets=[]
	for i,j in enumerate(jets.product()):
		if i>=maxjet: break
		if j.pt()<30: continue
		h_chsjet_npv.Fill(vertex.product().size())
		if not (j.genJet() == None):
			matched_gen_jets.append(j.genJet())
			matched_rec_jets.append(j)
			if j.genJet().pt()<20: continue
			h_chsjet_matched_npv.Fill(vertex.product().size())
	for i,j in enumerate(genjets.product()):
		if i>=maxjet: break
		if j.pt()<30: continue
		h_gen_chsjet_npv.Fill(vertex.product().size())
		if j in matched_gen_jets:
			if matched_rec_jets[matched_gen_jets.index(j)].pt()<20: continue
			h_gen_chsjet_matched_npv.Fill(vertex.product().size())
		else:
			continue

	###Puppi JETS
	matched_gen_jets=[]
	matched_rec_jets=[]
	for i,j in enumerate(pjets.product()):
		if i>=maxjet: break
		if j.pt()<30: continue
		h_puppijet_npv.Fill(vertex.product().size())
		if not (j.genJet() == None):
			matched_gen_jets.append(j.genJet())
			matched_rec_jets.append(j)
			if j.genJet().pt()<20: continue
			h_puppijet_matched_npv.Fill(vertex.product().size())
	for i,j in enumerate(genjets.product()):
		if i>=maxjet: break
		if j.pt()<30: continue
		h_gen_puppijet_npv.Fill(vertex.product().size())
		if j in matched_gen_jets:
			if matched_rec_jets[matched_gen_jets.index(j)].pt()<20: continue
			h_gen_puppijet_matched_npv.Fill(vertex.product().size())
		else:
			continue

	###New Puppi JETS
	###Note that this is not a slimmed jet collection, we need to gen matching by hand.
	matched_gen_jets=[]
	matched_rec_jets=[]
	for i,j in enumerate(njets.product()):
		if i>=maxjet: break
		if j.pt()<30: continue
		h_newpuppijet_npv.Fill(vertex.product().size())
		for gi, gj in enumerate (genjets.product()):
			dR = deltaR(j, gj)
			if dR > 0.2: continue 
			matched_gen_jets.append(gj)
			matched_rec_jets.append(j)
			if gj.pt()<20: continue
			h_newpuppijet_matched_npv.Fill(vertex.product().size())
	for i,j in enumerate(genjets.product()):
		if i>=maxjet: break
		if j.pt()<30: continue
		h_gen_newpuppijet_npv.Fill(vertex.product().size())
		if j in matched_gen_jets:
			if matched_rec_jets[matched_gen_jets.index(j)].pt()<20: continue			
			h_gen_newpuppijet_matched_npv.Fill(vertex.product().size())
		else:
			continue

prt_npv[0] = ROOT.TEfficiency(h_chsjet_matched_npv, h_chsjet_npv)
prt_npv[0].SetDirectory(ROOT.gDirectory);

prt_npv[1] = ROOT.TEfficiency(h_puppijet_matched_npv, h_puppijet_npv)
prt_npv[1].SetDirectory(ROOT.gDirectory);

prt_npv[2] = ROOT.TEfficiency(h_newpuppijet_matched_npv, h_newpuppijet_npv)
prt_npv[2].SetDirectory(ROOT.gDirectory);

eff_npv[0] = ROOT.TEfficiency(h_gen_chsjet_matched_npv, h_gen_chsjet_npv)
eff_npv[1] = ROOT.TEfficiency(h_gen_puppijet_matched_npv, h_gen_puppijet_npv)
eff_npv[2] = ROOT.TEfficiency(h_gen_newpuppijet_matched_npv, h_gen_newpuppijet_npv)

ROOT.gStyle.SetOptStat(0)


#Plot the histograms
def plot(hists,filename,xvarname,yvarname):
	c = ROOT.TCanvas("c","c",800,800) 
	colors=[ROOT.kCyan+1,ROOT.kBlue+1,ROOT.kMagenta+1,ROOT.kRed+1,ROOT.kOrange,ROOT.kYellow+1,ROOT.kGreen+1,ROOT.kGray] 
	legend=ROOT.TLegend(0.70,0.85,1,0.93)
	binedge=array('d',n.zeros(hists[0].GetPassedHistogram().GetNbinsX()))
	hists[0].GetPassedHistogram().GetXaxis().GetLowEdge(binedge)
	hframe=c.DrawFrame(binedge[0]-hists[0].GetPassedHistogram().GetBinWidth(0),0,binedge[-1]+2*hists[0].GetPassedHistogram().GetBinWidth(hists[0].GetPassedHistogram().GetNbinsX()),1.1,"")
	hframe.GetXaxis().SetTitle(xvarname)
	hframe.GetXaxis().SetTitleOffset(1.2)
	hframe.GetYaxis().SetTitle(yvarname)
	hframe.GetYaxis().SetTitleOffset(1.3)
	for ihist,hist in enumerate(hists):
		hist.SetLineColor(colors[ihist])
		hist.Draw("same")
		legend.AddEntry(hist, hist.GetPassedHistogram().GetTitle(),"lp")
	legend.Draw("same")
	if not os.path.exists("plots"): os.makedirs("plots")
	c.SaveAs("plots/"+filename+".png")
	c.SaveAs("plots/"+filename+".pdf")

outfile.cd()

prt_npv[0].Write()
prt_npv[1].Write()
prt_npv[2].Write()

eff_npv[0].Write()
eff_npv[1].Write()
eff_npv[2].Write()

plot(prt_npv, "purity_npv", "number of reconstructed vertices","Purity")
plot(eff_npv , "efficiency_npv" , "number of reconstructed vertices"     , "Efficiency")
