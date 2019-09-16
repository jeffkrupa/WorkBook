import FWCore.ParameterSet.Config as cms
from Configuration.StandardSequences.Eras import eras
process = cms.Process('PUPPI',eras.Run2_2018)

process.load('Configuration/StandardSequences/Services_cff')
process.load("FWCore.MessageService.MessageLogger_cfi")
process.load('Configuration/StandardSequences/FrontierConditions_GlobalTag_cff')
process.load("Configuration.StandardSequences.GeometryRecoDB_cff")

from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, 'auto:phase1_2018_realistic', '')

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(10000) )

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring(
        'root://cms-xrd-global.cern.ch//store/mc/RunIIAutumn18MiniAOD/QCD_Pt-15to7000_TuneCP5_Flat2018_13TeV_pythia8/MINIAODSIM/FlatPU0to70RAW_102X_upgrade2018_realistic_v15-v1/100000/010A1F3E-9169-7946-B65F-EE00F53E72B7.root'
    )
)

##import puppi setup
process.load('CommonTools/PileupAlgos/Puppi_cff')
from CommonTools.PileupAlgos.PhotonPuppi_cff        import setupPuppiPhoton 
from PhysicsTools.PatAlgos.slimming.puppiForMET_cff import makePuppiesFromMiniAOD
from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD

#enable the puppi from miniaod sequence
makePuppiesFromMiniAOD(process, True );

# unpack stored weights to save time recalculating it
process.puppi.candName = cms.InputTag('packedPFCandidates')
process.puppi.vertexName = cms.InputTag('offlineSlimmedPrimaryVertices')
process.puppi.clonePackedCands = cms.bool(True)
process.puppi.puppiDiagnostics = cms.bool(True)

# we want to recalculate PUPPI and also weights
process.puppi.useExistingWeights = cms.bool(False)
process.puppi.algos= cms.VPSet( 
                        cms.PSet( 
etaMin             = cms.vdouble(0.),
etaMax             = cms.vdouble(2.5),
ptMin              = cms.vdouble(0.),
MinNeutralPt       = cms.vdouble(0.2), #2016 tune
MinNeutralPtSlope  = cms.vdouble(0.015), #2016 tune
RMSEtaSF           = cms.vdouble(1.0),
MedEtaSF           = cms.vdouble(1.0),
EtaMaxExtrap       = cms.double(2.0),
puppiAlgos         = process.puppiCentral
),
                        cms.PSet( 
etaMin              = cms.vdouble( 2.5,  3.0),
etaMax              = cms.vdouble( 3.0, 10.0),
ptMin               = cms.vdouble( 0.0,  0.0),
MinNeutralPt        = cms.vdouble( 2.0,  2.0), #modified
MinNeutralPtSlope   = cms.vdouble(0.2, 0.13),  #modified
RMSEtaSF            = cms.vdouble(1.20, 0.95),
MedEtaSF            = cms.vdouble(0.90, 0.75),
EtaMaxExtrap        = cms.double( 2.0),
puppiAlgos          = process.puppiForward
))

#recluster met (automatically get jets)
runMetCorAndUncFromMiniAOD(process,
                           isData=False, 
                           metType="Puppi",
                           pfCandColl=cms.InputTag("puppiForMET"),
                           recoMetFromPFCs=True,  
                           jetFlavor="AK4PFPuppi",
                           postfix="Puppi" 
                           )
process.p = cms.Path(
    #process.fullPatMetSequence *
    process.egmPhotonIDSequence *
    process.puppiMETSequence * 
    process.fullPatMetSequencePuppi
    ) 

process.output = cms.OutputModule("PoolOutputModule",
                                  outputCommands = cms.untracked.vstring('keep *'),
                                  fileName       = cms.untracked.string ("ReminiAOD.root")
)
process.outpath  = cms.EndPath(process.output)

