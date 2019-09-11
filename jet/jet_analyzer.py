# import ROOT in batch mode
import sys
oldargv = sys.argv[:]
sys.argv = [ '-b-' ]
import ROOT
ROOT.gROOT.SetBatch(True)
sys.argv = oldargv

from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing('python')

#default options
options.inputFiles="root://cmsxrootd-site.fnal.gov//store/mc/RunIIAutumn18MiniAOD/QCD_Pt-15to7000_TuneCP5_Flat_13TeV_pythia8/MINIAODSIM/102X_upgrade2018_realistic_v15_ext1-v1/110000/8EF57574-29F7-DA4C-A5EC-8002BF2DEB96.root"
options.outputFile="jet.root"
options.maxEvents=-1

#overwrite if given any command line arguments
options.parseArguments()

# define deltaR
from math import hypot, pi, sqrt, fabs
import numpy as n

from jet_tree import *

# create an oput tree.

fout = ROOT.TFile (options.outputFile,"recreate")
t    = ROOT.TTree ("events","events")

declare_branches(t)

# load FWLite C++ libraries
ROOT.gSystem.Load("libFWCoreFWLite.so");
ROOT.gSystem.Load("libDataFormatsFWLite.so");
ROOT.FWLiteEnabler.enable()

# load FWlite python libraries
from DataFormats.FWLite import Handle, Events

jets, jetLabel      = Handle("std::vector<pat::Jet>"), "slimmedJets"
vertex, vertexLabel = Handle("std::vector<reco::Vertex>"),"offlineSlimmedPrimaryVertices"

# open file (you can use 'edmFileUtil -d /store/whatever.root' to get the physical file name)
#events = Events("file:/eos/cms/store/relval/CMSSW_9_4_0_pre3/RelValTTbar_13/MINIAODSIM/PU25ns_94X_mc2017_realistic_PixFailScenario_Run305081_FIXED_HS_AVE50-v1/10000/02B605A1-86C2-E711-A445-4C79BA28012B.root")
events = Events(options)

for ievent,event in enumerate(events):
    
    event.getByLabel(jetLabel, jets)
    event.getByLabel(vertexLabel, vertex)

    #print "\nEvent %d: run %6d, lumi %4d, event %12d" % (ievent,event.eventAuxiliary().run(), event.eventAuxiliary().luminosityBlock(),event.eventAuxiliary().event())

    nrun[0]   = event.eventAuxiliary().run()
    nlumi[0]  = event.eventAuxiliary().luminosityBlock()
    nevent[0] = event.eventAuxiliary().event()

    npv[0]    = vertex.product().size()
    njet[0]   = jets.product().size()

    ###CHS JETS
    for i,j in enumerate(jets.product()):

        if i>=maxjet: break

        jet_pt[i]  = j.pt()
        jet_eta[i] = j.eta()
        jet_phi[i] = j.phi()
        jet_energy[i]  = j.energy()

        rawjet_pt[i]  = j.pt()*j.jecFactor("Uncorrected")

        if not (j.genJet() == None):
            genjet_pt[i]  = j.genJet().pt()
            genjet_eta[i] = j.genJet().eta()
            genjet_phi[i] = j.genJet().phi()
            genjet_energy[i] = j.genJet().energy()

    t.Fill()


fout.Write()
fout.Close()
