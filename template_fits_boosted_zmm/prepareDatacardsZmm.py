import os
import sys
import glob
import argparse
import subprocess
import shutil
import time
import ROOT
import numpy as np
from array import array 

ROOT.gROOT.SetBatch(True)

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input-file', type=str, default='', help='input file with the templates');
parser.add_argument('-o', '--output-directory', type=str, default='', help='name of the output directory');
parser.add_argument('-y', '--year', type=str, default='2022', choices=['2022','2023','2022EE'], help='data taking period');
parser.add_argument('--mass-obs', type=str, default='mMuMu', help='mass observable to fit');
parser.add_argument('--rebin-pdf', type=int, default=10, help='rebin factor for pdf');
parser.add_argument('--rebin-data', type=int, default=2, help='rebin factor for data');
parser.add_argument('--mus-uncertainty', type=float, default=0.01, help='value of the dimuon pT scale uncertainty to be used');
parser.add_argument('--mur-uncertainty', type=float, default=0.05, help='value of the dimuon pT resolution uncertainty to be used');
parser.add_argument('--plot-bkg', action='store_true', help='plot the bkg pdf');
args = parser.parse_args()

lumi_dict = {
    '2022': 35.,
    '2022EE': 27.,
    '2023': 27.7
}
    
ROOT.gInterpreter.ProcessLine('#include "CMS_style.h"')
ROOT.setTDRStyle();
ROOT.gStyle.SetOptStat(0);
ROOT.RooMsgService.instance().setSilentMode(True);
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.ERROR) ;

os.system("mkdir -p "+args.output_directory);

def createCardTemplate(f_ws,cat="zmm",sys={},ws_name="w"):

    dc_name = "datacard_"+cat+".txt"

    f = open(dc_name,"w");
    f.write("imax * \n");
    f.write("jmax * \n");
    f.write("kmax * \n");
    f.write("------------ \n");
    f.write("shapes zmm "+cat+" "+f_ws+" "+ws_name+":"+"pdf_zmm \n");
    f.write("shapes bkg "+cat+" "+f_ws+" "+ws_name+":"+"pdf_bkg \n");
    f.write("shapes data_obs "+cat+" "+f_ws+" "+ws_name+":"+"data \n");
    f.write("------------ \n");
    f.write("bin "+cat+" \n");
    f.write("observation -1 \n");        
    f.write("------------ \n");
    f.write("bin "+cat+" "+cat+" \n");
    f.write("process  zmm   bkg \n");
    f.write("process  0     1   \n");
    f.write("rate  1   1  \n");
    f.write("------------ \n");
    f.write("lumi_13p6TeV  lnN  1.014  1.014 \n");
    if "QCD_scale_zjet" in sys:
        f.write("QCD_scale_zjet  lnN  %.2f  - \n"%(sys["QCD_scale_zjet"]));
    else:
        ## uncertainty on QCD taken from NLO Z+jets sample in genXsecAnalyzer                                                                                                        
        f.write("QCD_scale_zjet lnN  0.95/1.05  - \n");
    f.write("QCD_scale_bkg  lnN  -  0.93/1.06 \n");
    if "NLOEWK_corr_zjet" in sys:
        f.write("NLOEWK_corr_zjet lnN  %.2f  - \n"%(sys["NLOEWK_corr_zjet"]));
    else:
        f.write("NLOEWK_corr_zjet lnN  0.92/1.08  - \n");
    if "pdf_zjet" in sys:
        f.write("pdf_zjet lnN  %.2f  - \n"%(sys["pdf_zjet"]));
    else:
        f.write("pdf_zjet lnN  0.98/1.02  - \n");
    f.write("pdf_bkg  lnN  -   0.96/1.03  \n");
    f.write("CMS_scale_j  lnN  0.98/1.01  0.98/1.01 \n");
    f.write("CMS_res_j  lnN  0.99/1.01  0.99/1.01 \n");
    f.write("CMS_scale_m  lnN  0.99/1.02  0.98/1.02 \n");
    f.write("CMS_res_m  lnN  0.997/1.005  0.997/1.005 \n");
    f.write("CMS_trigger_m  lnN  0.99/1.02  0.99/1.02 \n");
    f.write("CMS_mus_unc param 0 1\n");
    f.write("CMS_mur_unc param 0 1\n");
    f.close()
    return dc_name;

def getChi2(h,h_fit):
    chi2 = 0;
    ndf  = 0;
    for i in range(0,h.GetNbinsX()):
        if h.GetBinContent(i+1) == 0 : continue;
        res = h.GetBinContent(i+1)-h_fit.GetBinContent(i+1);
        chi2 += (res**2)/(h.GetBinError(i+1)**2);
        ndf = ndf + 1;
    return chi2,ndf;

def getMaxAndHWHM(h):
    binMax = h.GetMaximumBin();
    xMax = h.GetXaxis().GetBinCenter(binMax);
    yMax = h.GetBinContent(binMax);    
    halfMax = yMax / 2.0;
    binLeft = binMax;
    while binLeft > 1 and h.GetBinContent(binLeft) > halfMax:
        binLeft = binLeft-1;
    binRight = binMax;
    while binRight > 1 and h.GetBinContent(binRight) > halfMax:
        binRight = binRight+1;

    xLeft=h.GetXaxis().GetBinCenter(binLeft);
    xRight=h.GetXaxis().GetBinCenter(binRight);
    hwhm = (xRight-xLeft)/2.

    return xMax,hwhm

f_input_zmm = ROOT.TFile(args.input_file,"READ");

h_zmm = f_input_zmm.Get("DY");
h_vv = f_input_zmm.Get("VV");
h_top = f_input_zmm.Get("TT");
h_data = f_input_zmm.Get("data_obs");
    
obs = ROOT.RooRealVar(args.mass_obs,"",h_data.GetXaxis().GetBinCenter(h_data.GetMaximumBin()),h_data.GetXaxis().GetXmin(),h_data.GetXaxis().GetXmax())
obs.setBins(h_data.GetNbinsX());
obs_list = ROOT.RooArgList();
obs_list.add(obs);

w = ROOT.RooWorkspace("w","");

## data histogram conversion
rh_data = ROOT.RooDataHist("data","",obs_list,h_data)
w.Import(rh_data);

label = ROOT.TLatex();
label.SetTextAlign(12);
label.SetNDC();
label.SetTextSize(label.GetTextSize()*0.8);

c = ROOT.TCanvas("c","",600,600);

###################
## ZMM modelling ##
###################

rh_zmm = ROOT.RooDataHist("zmm","",obs_list,h_zmm)

## Relativistic Breit-Wigner
zmm_mz = ROOT.RooRealVar("zmm_mz","zmm_mz",91.18);
zmm_gammaz = ROOT.RooRealVar("zmm_gammaz","zmm_gammaz",2.49);
pdf_zmm_bw = ROOT.RooGenericPdf("pdf_zmm_bw","pdf_zmm_bw","@0/(pow(@0*@0 - @1*@1,2) + @2*@2*@0*@0*@0*@0/(@1*@1))",ROOT.RooArgList(obs,zmm_mz,zmm_gammaz));

## fix the Z-boson PDG parameters
zmm_mz.setConstant(True);
zmm_gammaz.setConstant(True);

## Gaussian resolution
CMS_mus_unc = ROOT.RooRealVar("CMS_mus_unc","CMS_mus_unc",0.,-5.,5.);
CMS_mur_unc = ROOT.RooRealVar("CMS_mur_unc","CMS_mur_unc",0.,-5.,5.);
zmm_mus_unc = ROOT.RooRealVar("zmm_mus_unc","zmm_mus_unc",args.mus_uncertainty);
zmm_mur_unc = ROOT.RooRealVar("zmm_mur_unc","zjet_mur_unc",args.mur_uncertainty);
CMS_mus_unc.setConstant(True);
CMS_mur_unc.setConstant(True);
zmm_mus_unc.setConstant(True);
zmm_mur_unc.setConstant(True);

zmm_gmean = ROOT.RooRealVar("zmm_gmean","zmm_gmean",0.,-20,20);
zmm_gsigmaL = ROOT.RooRealVar("zmm_gsigmaL","zmm_gsigmaL",2.5,1,15);
zmm_gsigmaR = ROOT.RooRealVar("zmm_gsigmaR","zmm_gsigmaR",2.5,1,15);

zmm_gpeak = ROOT.RooFormulaVar("zmm_gpeak","","@0*(1+@1*(@0+@3)*@2)",ROOT.RooArgList(zmm_gmean,zmm_mus_unc,CMS_mus_unc,zmm_mz))
zmm_gresoL = ROOT.RooFormulaVar("zmm_gresoL","","@0*(1+@1*@2)",ROOT.RooArgList(zmm_gsigmaL,zmm_mur_unc,CMS_mur_unc))
zmm_gresoR = ROOT.RooFormulaVar("zmm_gresoR","","@0*(1+@1*@2)",ROOT.RooArgList(zmm_gsigmaR,zmm_mur_unc,CMS_mur_unc))
pdf_zmm_reso = ROOT.RooBifurGauss("pdf_zmm_reso","pdf_zmm_reso",obs,zmm_gpeak,zmm_gresoL,zmm_gresoR)

pdf_zmm_sig = ROOT.RooFFTConvPdf("pdf_zmm_sig","pdf_zmm_sig",obs,pdf_zmm_bw,pdf_zmm_reso);

## Combinatorial background
zmm_coef_1 = ROOT.RooRealVar("zmm_coef_1","zmm_coef_1",0.001,-10,10)
zmm_coef_2 = ROOT.RooRealVar("zmm_coef_2","zmm_coef_2",0.001,-10,10)
zmm_coef_3 = ROOT.RooRealVar("zmm_coef_3","zmm_coef_3",0.001,-10,10)
pdf_zmm_bkg = ROOT.RooChebychev("pdf_zmm_bkg","",obs,ROOT.RooArgList(zmm_coef_1,zmm_coef_2,zmm_coef_3));

## Final pdf
zmm_frac = ROOT.RooRealVar("zmm_frac","zmm_frac",0.1,0.,1.);
zmm_frac_fail = ROOT.RooRealVar("zmm_frac_fail","zmm_frac_fail",0.1,0.,1.);    
pdf_zmm = ROOT.RooAddPdf("pdf_zmm","pdf_zmm",ROOT.RooArgList(pdf_zmm_sig,pdf_zmm_bkg),ROOT.RooArgList(zmm_frac),True);

## Fit and set parameters
fit_zmm_res = pdf_zmm.fitTo(rh_zmm,ROOT.RooFit.Save(),ROOT.RooFit.Optimize(1),ROOT.RooFit.SumW2Error(True),ROOT.RooFit.Minimizer("Minuit2"));
pdf_zmm_norm = ROOT.RooRealVar(pdf_zmm.GetName()+"_norm","",rh_zmm.sumEntries())
pdf_zmm_norm.setConstant(True);
zmm_coef_1.setConstant(True);
zmm_coef_2.setConstant(True);
zmm_coef_3.setConstant(True);
zmm_gmean.setConstant(True);
zmm_gsigmaL.setConstant(True);
zmm_gsigmaR.setConstant(True);
zmm_frac.setConstant(True);
CMS_mus_unc.setConstant(False);
CMS_mur_unc.setConstant(False);

## plotting part
h_fit_zmm = pdf_zmm.createHistogram("h_fit_zmm",obs,ROOT.RooFit.Binning(obs.getBins()*args.rebin_pdf));
h_fit_zmm.Scale(pdf_zmm_norm.getVal()*args.rebin_pdf);
h_fit_zmm_bkg = pdf_zmm_bkg.createHistogram("h_fit_zmm_bkg",obs,ROOT.RooFit.Binning(obs.getBins()*args.rebin_pdf));
h_fit_zmm_bkg.Scale(pdf_zmm_norm.getVal()*args.rebin_pdf*(1-zmm_frac.getVal()));
h_fit_zmm_sig = pdf_zmm_sig.createHistogram("h_fit_zmm_sig",obs,ROOT.RooFit.Binning(obs.getBins()*args.rebin_pdf));
h_fit_zmm_sig.Scale(pdf_zmm_norm.getVal()*args.rebin_pdf*zmm_frac.getVal());
h_fit_zmm_test = pdf_zmm.createHistogram("h_fit_zmm_test",obs);
h_fit_zmm_test.Scale(pdf_zmm_norm.getVal());
chi2_zmm,ndf_zmm = getChi2(h_zmm,h_fit_zmm_test);
chi2_zmm = chi2_zmm/(ndf_zmm-fit_zmm_res.floatParsFinal().getSize());
max_zmm, hwhm_zmm = getMaxAndHWHM(h_fit_zmm_sig);

## import in the zmm
w.Import(pdf_zmm);
w.Import(pdf_zmm_norm);

h_zmm.GetXaxis().SetTitle(args.mass_obs+" (GeV)");
h_zmm.GetYaxis().SetTitle("Events");
h_zmm.SetMarkerColor(ROOT.kBlack);
h_zmm.SetLineColor(ROOT.kBlack);
h_zmm.SetMarkerSize(0.6);
h_zmm.SetMarkerStyle(20);
h_zmm.Rebin(args.rebin_data);
h_zmm.GetYaxis().SetRangeUser(0.,h_zmm.GetMaximum()*1.25);
h_zmm.Draw("EP");
h_fit_zmm_bkg.SetLineColor(ROOT.kBlue);
h_fit_zmm_bkg.SetLineWidth(2);
h_fit_zmm_bkg.Scale(args.rebin_data);
if args.plot_bkg:
    h_fit_zmm_bkg.Draw("hist same");
h_fit_zmm.SetLineColor(ROOT.kRed);
h_fit_zmm.SetLineWidth(2);
h_fit_zmm.Scale(args.rebin_data);
h_fit_zmm.Draw("hist same");
h_zmm.Draw("EPsame");
ROOT.CMS_lumi(c,"%.1f"%(lumi_dict[args.year]),False,False,True);
label.DrawLatex(0.65,0.8,"#chi^{2}/ndf=%.2f"%(chi2_zmm));
label.DrawLatex(0.65,0.75,"Peak=%.2f"%(max_zmm))
label.DrawLatex(0.65,0.7,"HWHM=%.2f"%(hwhm_zmm));
c.SaveAs(args.output_directory+"/zmm_fit.png","png");
c.SaveAs(args.output_directory+"/zmm_fit.pdf","pdf");

###################
## Bkg modelling ##
###################

h_bkg = h_vv.Clone();
h_bkg.SetName("h_bkg");
h_bkg.Add(h_top);

rh_bkg = ROOT.RooDataHist("bkg","",obs_list,h_bkg)

## Z boson lineshape
bkg_mz = ROOT.RooRealVar("bkg_mz","bkg_mz",91.18);
bkg_gammaz = ROOT.RooRealVar("bkg_gammaz","bkg_gammaz",2.49);
pdf_bkg_bw = ROOT.RooGenericPdf("pdf_bkg_bw","pdf_bkg_bw","@0/(pow(@0*@0 - @1*@1,2) + @2*@2*@0*@0*@0*@0/(@1*@1))",ROOT.RooArgList(obs,bkg_mz,bkg_gammaz));
bkg_mz.setConstant(True);
bkg_gammaz.setConstant(True);
bkg_mus_unc = ROOT.RooRealVar("bkg_mus_unc","bkg_mus_unc",args.mus_uncertainty);
bkg_mur_unc = ROOT.RooRealVar("bkg_mur_unc","bkg_mur_unc",args.mur_uncertainty);
bkg_mus_unc.setConstant(True);
bkg_mur_unc.setConstant(True);

CMS_mus_unc.setConstant(True);
CMS_mur_unc.setConstant(True);

## z boson lineshape
bkg_mean_gaus = ROOT.RooRealVar("bkg_mean_gaus","bkg_mean_gaus",0,-10,10);
bkg_sigma_gaus = ROOT.RooRealVar("bkg_sigma_gaus","bkg_sigma_gaus",1.5,0.5,10);
bkg_peak = ROOT.RooFormulaVar("bkg_peak","","@0*(1+@1*(@0+@3)*@2)",ROOT.RooArgList(bkg_mean_gaus,bkg_mus_unc,CMS_mus_unc,bkg_mz))
bkg_sigma = ROOT.RooFormulaVar("bkg_sigma","","@0*(1+@1*@2)",ROOT.RooArgList(bkg_sigma_gaus,bkg_mur_unc,CMS_mur_unc))
pdf_bkg_gaus = ROOT.RooGaussian("pdf_bkg_gaus","pdf_bkg_gaus",obs,bkg_peak,bkg_sigma)
pdf_bkg_sig = ROOT.RooFFTConvPdf("pdf_bkg_sig","pdf_bkg_sig",obs,pdf_bkg_bw,pdf_bkg_gaus);

bkg_coef_1 = ROOT.RooRealVar("bkg_coef_1","bkg_coef_1",0.001,-10,10)
bkg_coef_2 = ROOT.RooRealVar("bkg_coef_2","bkg_coef_2",0.001,-10,10)
bkg_coef_3 = ROOT.RooRealVar("bkg_coef_3","bkg_coef_3",0.001,-10,10)
pdf_bkg_bkg = ROOT.RooChebychev("pdf_bkg_bkg","",obs,ROOT.RooArgList(bkg_coef_1,bkg_coef_2,bkg_coef_3));

bkg_frac = ROOT.RooRealVar("bkg_frac","bkg_frac",0.1,0.,1.);
pdf_bkg = ROOT.RooAddPdf("pdf_bkg","pdf_bkg",ROOT.RooArgList(pdf_bkg_sig,pdf_bkg_bkg),ROOT.RooArgList(bkg_frac),True);

## final fit and normalization
fit_bkg_res = pdf_bkg.fitTo(rh_bkg,ROOT.RooFit.Save(),ROOT.RooFit.Optimize(1),ROOT.RooFit.SumW2Error(True),ROOT.RooFit.Minimizer("Minuit2"));
pdf_bkg_norm = ROOT.RooRealVar(pdf_bkg.GetName()+"_norm","",rh_bkg.sumEntries())
pdf_bkg_norm.setConstant(True);
bkg_coef_1.setConstant(True);
bkg_coef_2.setConstant(True);
bkg_coef_3.setConstant(True);
bkg_mean_gaus.setConstant(True);
bkg_sigma_gaus.setConstant(True);
bkg_frac.setConstant(True);
CMS_mus_unc.setConstant(False);
CMS_mur_unc.setConstant(False);

h_fit_bkg_bkg = pdf_bkg_bkg.createHistogram("h_fit_bkg_bkg",obs,ROOT.RooFit.Binning(obs.getBins()*args.rebin_pdf));
h_fit_bkg_bkg.Scale(pdf_bkg_norm.getVal()*args.rebin_pdf*(1-bkg_frac.getVal()));
h_fit_bkg_sig = pdf_bkg_sig.createHistogram("h_fit_bkg_sig",obs,ROOT.RooFit.Binning(obs.getBins()*args.rebin_pdf));
h_fit_bkg_sig.Scale(pdf_bkg_norm.getVal()*args.rebin_pdf*bkg_frac.getVal());
h_fit_bkg = pdf_bkg.createHistogram("h_fit_bkg",obs,ROOT.RooFit.Binning(obs.getBins()*args.rebin_pdf));
h_fit_bkg.Scale(pdf_bkg_norm.getVal()*args.rebin_pdf);

h_fit_bkg_test = pdf_bkg.createHistogram("h_fit_bkg_test",obs);
h_fit_bkg_test.Scale(pdf_bkg_norm.getVal());
chi2_bkg, ndf_bkg = getChi2(h_bkg,h_fit_bkg_test);
chi2_bkg = chi2_bkg/(ndf_bkg-fit_bkg_res.floatParsFinal().getSize());
max_bkg, hwhm_bkg = getMaxAndHWHM(h_fit_bkg_sig);
    
w.Import(pdf_bkg);
w.Import(pdf_bkg_norm);

h_bkg.GetXaxis().SetTitle(args.mass_obs+" (GeV)");
h_bkg.GetYaxis().SetTitle("Events");
h_bkg.SetMarkerColor(ROOT.kBlack);
h_bkg.SetLineColor(ROOT.kBlack);
h_bkg.SetMarkerSize(0.6);
h_bkg.SetMarkerStyle(20);
h_bkg.Rebin(args.rebin_data);
h_bkg.GetYaxis().SetRangeUser(0.,h_bkg.GetMaximum()*1.25);
h_bkg.Draw("EP");
h_fit_bkg_bkg.SetLineColor(ROOT.kBlue);
h_fit_bkg_bkg.SetLineWidth(2);
h_fit_bkg_bkg.Scale(args.rebin_data);
if args.plot_bkg:
    h_fit_bkg_bkg.Draw("hist same");
h_fit_bkg.SetLineColor(ROOT.kRed);
h_fit_bkg.SetLineWidth(2);
h_fit_bkg.Scale(args.rebin_data);
h_fit_bkg.Draw("hist same");
h_bkg.Draw("EPsame");
ROOT.CMS_lumi(c,"%.1f"%(lumi_dict[args.year]),False,False,True);
label.DrawLatex(0.65,0.8,"#chi^{2}/ndf=%.2f"%(chi2_bkg));
label.DrawLatex(0.65,0.75,"Peak=%.2f"%(max_bkg))
label.DrawLatex(0.65,0.7,"HWHM=%.2f"%(hwhm_bkg));
c.SaveAs(args.output_directory+"/bkg_fit.png","png");
c.SaveAs(args.output_directory+"/bkg_fit.pdf","pdf");

### Save output files
f_out = ROOT.TFile(args.output_directory+"/workspace_zmm.root","RECREATE");
f_out.cd()
w.Write("w");
f_out.Close();

### write datacard
os.chdir(args.output_directory);
sys={}
dc = createCardTemplate("workspace_zmm.root","zmm",sys,"w");

