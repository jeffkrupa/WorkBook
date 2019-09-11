import numpy as n

maxjet = 10000
    
    #event information
nrun       = n.zeros(1,dtype=int)
nlumi      = n.zeros(1,dtype=int)
nevent     = n.zeros(1,dtype=float)
npv        = n.zeros(1,dtype=int)

    #jet information
njet       = n.zeros(1,dtype=int)
jet_pt     = n.zeros(maxjet,dtype=float)
jet_energy = n.zeros(maxjet,dtype=float)
jet_eta    = n.zeros(maxjet,dtype=float)
jet_phi    = n.zeros(maxjet,dtype=float)
genjet_pt  = n.zeros(maxjet,dtype=float)
genjet_energy = n.zeros(maxjet,dtype=float)
genjet_eta = n.zeros(maxjet,dtype=float)
genjet_phi = n.zeros(maxjet,dtype=float)
rawjet_pt  = n.zeros(maxjet,dtype=float)
    
def declare_branches(t):

    t.Branch("run", nrun, 'run/I')
    t.Branch("lumi", nlumi, 'lumi/I')
    t.Branch("event", nevent, 'event/D')

    t.Branch("npv", npv, 'npv/I')
    t.Branch("njet", njet, 'njet/I')

    t.Branch("jet_pt",jet_pt,'jet_pt[njet]/D')
    t.Branch("jet_energy",jet_energy,'jet_energy[njet]/D')
    t.Branch("jet_eta",jet_eta,'jet_eta[njet]/D')
    t.Branch("jet_phi",jet_phi,'jet_phi[njet]/D')

    t.Branch("genjet_pt",genjet_pt,'genjet_pt[njet]/D')
    t.Branch("genjet_energy",genjet_energy,'genjet_energy[njet]/D')
    t.Branch("genjet_eta",genjet_eta,'genjet_eta[njet]/D')
    t.Branch("genjet_phi",genjet_phi,'genjet_phi[njet]/D')

    t.Branch("rawjet_pt",rawjet_pt,'rawjet_pt[njet]/D')

    print "All branches configured"
