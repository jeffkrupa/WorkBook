# import ROOT in batch mode
from DataFormats.FWLite import Handle, Events
import numpy as np
import sys
import os
import time
from array import array
from math import hypot, pi, sqrt, fabs
import ROOT
import re


ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gSystem.Load("libFWCoreFWLite.so")
ROOT.gSystem.Load("libDataFormatsFWLite.so")
ROOT.FWLiteEnabler.enable()
ROOT.TH1.SetDefaultSumw2()


# Plot the histograms
def plot(hists, filename, xvarname, yvarname):
    c = ROOT.TCanvas("c", "c", 800, 800)
    colors = [  ROOT.kCyan+1,
                ROOT.kBlue+1,
                ROOT.kMagenta+1 ]
    legend = ROOT.TLegend(0.70, 0.85, 1, 0.93)
    binedge = array('d', np.zeros(hists[0].GetPassedHistogram().GetNbinsX()))
    hists[0].GetPassedHistogram().GetXaxis().GetLowEdge(binedge)

    # Aesthetics
    hframe = c.DrawFrame(0, 0, 70, 1.1, "")
    hframe.GetXaxis().SetTitle(xvarname)
    hframe.GetXaxis().SetTitleOffset(1.2)
    hframe.GetYaxis().SetTitle(yvarname)
    hframe.GetYaxis().SetTitleOffset(1.3)

    # Draw the histograms
    for color, hist in zip(colors, hists):
        hist.SetLineColor(color)
        hist.SetLineWidth(2)
        hist.Draw("same")
        name = re.sub('.*npv_','',hist.GetPassedHistogram().GetTitle())
        legend.AddEntry(hist, name, "lp")

    legend.Draw("same")
    if not os.path.exists("plots"):
        os.makedirs("plots")
    c.SaveAs("plots/"+filename+".png")
    c.SaveAs("plots/"+filename+".pdf")



def print_same_line(s):
    sys.stdout.write(s)
    sys.stdout.flush()
    sys.stdout.write((b'\x08' * len(s)).decode())  # back n chars


def deltaPhi(a, b):
    '''Calculate delta phi between two candidates'''
    dphi = abs(a.phi() - b.phi())
    if (dphi <= pi):
        return dphi
    else:
        return 2*pi - dphi

def deltaR(a, b):
    '''Calulate delta R between two candidates'''
    dphi = deltaPhi(a, b)
    return hypot(a.eta()-b.eta(), dphi)

def find_matching_jet(one_jet, many_jets):
    for j in many_jets:
        if deltaR(j, one_jet) < 0.4:
            return j
    return None

def fill_histograms(recjets, genjets, nvtx, h_npv, h_matched_npv, h_gen_npv, h_gen_matched_npv):

    ### Purity
    # Loop over reconstructed jets
    # and check how often they have a
    # matching gen jet
    for recjet in recjets:
        # Jet PT cut
        if recjet.pt() < 30:
            continue

        # Denominator: all jets passing pt cut
        h_npv.Fill(nvtx)

        # Numerator: matched jets passing pt cut
        matching_gen_jet = find_matching_jet(recjet, genjets)
        if matching_gen_jet and matching_gen_jet.pt() > 20:
                h_matched_npv.Fill(nvtx)

    ### Efficiency
    # Loop over gen jets
    # and check how often they have a
    # they have a matching reco jet
    for genjet in genjets:
        # PT cut
        if genjet.pt() < 30:
            continue

        # Denominator: All gen jets passing pt cut
        h_gen_npv.Fill(nvtx)

        # Numerator: matched gen jets passing pt cut
        matching_rec_jet = find_matching_jet(genjet, recjets)
        if matching_rec_jet and matching_rec_jet.pt() > 20:
            h_gen_matched_npv.Fill(nvtx)

def main():

    # All the inputs we need to retrieve the EDM collections from MiniAOD
    jet_handle, jet_label = Handle("std::vector<pat::Jet>"), "slimmedJets"
    pjet_handle, pjet_label = Handle("std::vector<pat::Jet>"), "slimmedJetsPuppi"
    njet_handle, njet_label = Handle("std::vector<pat::Jet>"), "patJetsPuppi"
    vertex_handle, vertex_label = Handle("std::vector<reco::Vertex>"), "offlineSlimmedPrimaryVertices"
    genjet_handle, genjet_label = Handle("std::vector<reco::GenJet>"), "slimmedGenJets"

    # Initialize histograms
    npv_bins = np.arange(0, 70, 7)
    def make_npv_hist(title):
        h = ROOT.TH1F(title, title, len(npv_bins)-1, array('d',npv_bins))
        h.SetDirectory(0)
        return h
    # for purity

    h_chsjet_npv                = make_npv_hist("recojets_npv_CHS")
    h_chsjet_matched_npv        = make_npv_hist("matchedrecojets_npv_CHS")
    h_puppijet_npv              = make_npv_hist("recojets_npv_PUPPI")
    h_puppijet_matched_npv      = make_npv_hist("matchedrecojets_npv_PUPPI")
    h_newpuppijet_npv           = make_npv_hist("recojets_npv_newPUPPI")
    h_newpuppijet_matched_npv   = make_npv_hist("matchedrecojets_npv_newPUPPI")

    # for efficiency
    h_gen_chsjet_npv                = make_npv_hist("genjets_npv_CHS")
    h_gen_chsjet_matched_npv        = make_npv_hist("matchedgenjets_npv_CHS")
    h_gen_puppijet_npv              = make_npv_hist("genjets_npv_PUPPI")
    h_gen_puppijet_matched_npv      = make_npv_hist("matchedgenjets_npv_PUPPI")
    h_gen_newpuppijet_npv           = make_npv_hist("genjets_npv_newPUPPI")
    h_gen_newpuppijet_matched_npv   = make_npv_hist( "matchedgenjets_npv_newPUPPI")

    events = Events("root://cmsxrootd.fnal.gov//store/user/aandreas/share/jumpshot/ReminiAOD.root")
    nevents = int(events.size())
    print "total events: ", nevents


    for ievent, event in enumerate(events):
        print_same_line(str(round(100.*ievent/nevents, 2))+'%')

        # Retrieve collections
        event.getByLabel(jet_label, jet_handle)
        event.getByLabel(pjet_label, pjet_handle)
        event.getByLabel(njet_label, njet_handle)
        event.getByLabel(genjet_label, genjet_handle)
        event.getByLabel(vertex_label, vertex_handle)

        # Unpack for easier handling
        nvtx = vertex_handle.product().size()
        genjets = genjet_handle.product()
        jets = jet_handle.product()
        pjets = pjet_handle.product()
        njets = njet_handle.product()

        # CHS jets
        fill_histograms(jets, genjets, nvtx, h_chsjet_npv, h_chsjet_matched_npv, h_gen_chsjet_npv, h_gen_chsjet_matched_npv)

        # Puppi jets
        fill_histograms(pjets, genjets, nvtx, h_puppijet_npv, h_puppijet_matched_npv, h_gen_puppijet_npv, h_gen_puppijet_matched_npv)

        # New puppi jets
        fill_histograms(njets, genjets, nvtx, h_newpuppijet_npv, h_newpuppijet_matched_npv, h_gen_newpuppijet_npv, h_gen_newpuppijet_matched_npv)


    # Plug our numerator and denominator histograms into TEfficiency
    # and run a quick plotting code
    prt_npv = []
    prt_npv.append(ROOT.TEfficiency(h_chsjet_matched_npv, h_chsjet_npv))
    prt_npv.append(ROOT.TEfficiency(h_puppijet_matched_npv, h_puppijet_npv))
    prt_npv.append(ROOT.TEfficiency(h_newpuppijet_matched_npv, h_newpuppijet_npv))
    plot(prt_npv, "purity_npv", "number of reconstructed vertices", "Purity")

    # Same for efficiency
    eff_npv = []
    eff_npv.append(ROOT.TEfficiency(h_gen_chsjet_matched_npv, h_gen_chsjet_npv))
    eff_npv.append(ROOT.TEfficiency(h_gen_puppijet_matched_npv, h_gen_puppijet_npv))
    eff_npv.append(ROOT.TEfficiency(h_gen_newpuppijet_matched_npv, h_gen_newpuppijet_npv))
    plot(eff_npv, "efficiency_npv", "number of reconstructed vertices", "Efficiency")





if __name__ == "__main__":
    main()