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
parser.add_argument('-i', '--input-dir', type=str, default='', help='input directory with files');
parser.add_argument('-c', '--cat-id', type=str, default='tutorial', choices=['cat0','cat1','cat2','cat3','cat4'], help='category identifier');
parser.add_argument('-o', '--output-directory', type=str, default='', help='name of the output directory');
parser.add_argument('-t', '--tagger', type=str, default='gpart', choices=['pnet','gpart'], help='tagger to be considered');
parser.add_argument('-s', '--sum-matched-unmatched', action='store_true', help='sum matched and umatched. Default is unmatched go in QCD backgorund');
parser.add_argument('-y', '--year', type=str, default='2022', choices=['2022','2023'], help='data taking period');
parser.add_argument('--mass-obs', type=str, default='gpart_mass', help='mass observable to fit');
parser.add_argument('--rebin-pdf', type=int, default=10, help='rebin factor for pdf');
parser.add_argument('--rebin-data', type=int, default=2, help='rebin factor for data');
parser.add_argument('--jms-uncertainty', type=float, default=0.03, help='value of the jet mass scale uncertainty to be used');
parser.add_argument('--jmr-uncertainty', type=float, default=0.10, help='value of the jet mass resolution uncertainty to be used');
parser.add_argument('--float-mass-peak', action='store_true', help='float peak position');
parser.add_argument('--float-mass-reso', action='store_true', help='float peak resolution');
parser.add_argument('--use-poly-bkg', action='store_true', help='use polynomial background for pass cat0 and cat1 instead of a gaussian');
parser.add_argument('--plot-bkg', action='store_true', help='plot the bkg pdf');
args = parser.parse_args()

lumi_dict = {
    '2022': 35.,
    '2023': 27.7
}
    
ROOT.gInterpreter.ProcessLine('#include "CMS_style.h"')
ROOT.setTDRStyle();
ROOT.gStyle.SetOptStat(0);
ROOT.RooMsgService.instance().setSilentMode(True);
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.ERROR);
os.system("mkdir -p "+args.output_directory);
os.system("mkdir -p workspace");
def rebin_histogram(h, new_name=None):
    # Create new histogram from 50 to 150 GeV with 100 bins
    h_new = ROOT.TH1F(new_name or h.GetName(), h.GetTitle(), 100, 50, 150)

    # Fill new histogram with content from bins 11 to 110 (1-based indexing in ROOT)
    for i in range(11, 111):  # bins 11 to 110 inclusive
        bin_center = h.GetBinCenter(i)
        bin_content = h.GetBinContent(i)
        bin_error = h.GetBinError(i)
        new_bin = h_new.FindBin(bin_center)
        h_new.SetBinContent(new_bin, bin_content)
        h_new.SetBinError(new_bin, bin_error)

    return h_new

def createCardTemplate(cat_score,cat_sel,f_ws,sys={},ws_name="w"):

    dc_name = "datacard_zbb_"+cat_score+"_"+cat_sel+".txt"

    f = open(dc_name,"w");
    f.write("imax * \n");
    f.write("jmax * \n");
    f.write("kmax * \n");
    f.write("------------ \n");
    f.write("shapes zjet "+cat_sel+" "+f_ws+" "+ws_name+":"+"pdf_zjet_"+cat_sel+"\n");
    f.write("shapes wjet "+cat_sel+" "+f_ws+" "+ws_name+":"+"pdf_wjet_"+cat_sel+"\n");
    f.write("shapes qcd "+cat_sel+" "+f_ws+" "+ws_name+":"+"pdf_qcd_"+cat_sel+"\n");
    f.write("shapes data_obs "+cat_sel+" "+f_ws+" "+ws_name+":"+"data_"+cat_sel+"\n");
    f.write("------------ \n");
    f.write("bin   "+cat_sel+" \n");
    f.write("observation -1 \n");        
    f.write("------------ \n");
    f.write("bin   "+cat_sel+" "+cat_sel+" "+cat_sel+" \n");
    f.write("process   zjet  wjet  qcd \n");
    f.write("process   0     1     2 \n");
    f.write("rate   1     1     1 \n");
    f.write("------------ \n");
    f.write("lumi_13p6TeV  lnN  1.014  1.014  -\n");
    if "QCD_scale_zjet" in sys:
        f.write("QCD_scale_zjet  lnN  %.2f  -  -\n"%(sys["QCD_scale_zjet"]));
    else:
        ## uncertainty on QCD taken from NLO Z+jets sample in genXsecAnalyzer
        f.write("QCD_scale_zjet  lnN  0.94/1.05  -  -\n");
    if "QCD_scale_wjet" in sys:
        f.write("QCD_scale_wjet  lnN  -  %.2f  -\n"%(sys["QCD_scale_wjet"]));
    else:
        ## uncertainty on QCD taken from NLO W+jets sample in genXsecAnalyzer
        f.write("QCD_scale_wjet  lnN  -  0.95/1.05  -\n");
    if "NLOEWK_corr_zjet" in sys:
        f.write("NLOEWK_corr_zjet  lnN  %.2f  -  -\n"%(sys["NLOEWK_corr_zjet"]));
    else:
        f.write("NLOEWK_corr_zjet  lnN  0.92/1.09  -  -\n");
    if "NLOEWK_corr_wjet" in sys:
        f.write("NLOEWK_corr_wjet  lnN  -  %.2f  -\n"%(sys["NLOEWK_corr_zjet"]));
    else:        
        f.write("NLOEWK_corr_wjet  lnN  -  0.92/1.09  -\n");
    if "pdf_zjet" in sys:
        f.write("pdf_zjet lnN  %.2f  -  -\n"%(sys["pdf_zjet"]));
    else:
        f.write("pdf_zjet lnN  0.98/1.02  -  -\n");
    if "pdf_wjet" in sys:
        f.write("pdf_wjet lnN  -  %.2f  -\n"%(sys["pdf_wjet"]));
    else:
        f.write("pdf_wjet lnN  -  0.98/1.02  -\n");
    f.write("CMS_scale_j  lnN  0.97/1.03 0.96/1.04  -\n");
    f.write("CMS_res_j  lnN  0.98/1.01   0.97/1.02  -\n");
    f.write("CMS_trigger_zbb  lnN  0.98/1.02  0.97/1.02  -\n");
    if args.float_mass_peak:
        f.write("CMS_jms_unc flatParam\n");
    else:
        f.write("CMS_jms_unc param 0 1\n");
    if args.float_mass_reso:
        f.write("CMS_jmr_unc flatParam\n");
    else:
        f.write("CMS_jmr_unc param 0 1\n");
        
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

if args.year == "2022":
    f_zjet = ROOT.TFile(args.input_dir+"/Zto2Q_2022.root","READ");
    f_wjet = ROOT.TFile(args.input_dir+"/Wto2Q_2022.root","READ");
    f_qcd = ROOT.TFile(args.input_dir+"/QCD_2022.root","READ");
    f_data = ROOT.TFile(args.input_dir+"/JetMET_2022.root","READ");
elif args.year == "2023":
    f_zjet = ROOT.TFile(args.input_dir+"/Zto2Q_2023.root","READ");
    f_wjet = ROOT.TFile(args.input_dir+"/Wto2Q_2023.root","READ");
    f_qcd = ROOT.TFile(args.input_dir+"/QCD_2023.root","READ");
    f_data = ROOT.TFile(args.input_dir+"/JetMET_2023.root","READ");

h_zjet_pass = f_zjet.Get("hist_ak8_"+args.mass_obs);
h_wjet_pass = f_wjet.Get("hist_ak8_"+args.mass_obs);
h_qcd_pass = f_qcd.Get("hist_ak8_"+args.mass_obs);
h_data_pass = f_data.Get("hist_ak8_"+args.mass_obs);

obs = ROOT.RooRealVar(args.mass_obs,"",h_data_pass.GetXaxis().GetBinCenter(h_data_pass.GetMaximumBin()),h_data_pass.GetXaxis().GetXmin(),h_data_pass.GetXaxis().GetXmax())
obs.setBins(h_data_pass.GetNbinsX());
obs_list = ROOT.RooArgList();
obs_list.add(obs);

w_pass = ROOT.RooWorkspace("w_pass","");

## data histogram conversion
rh_data_pass = ROOT.RooDataHist("data_pass","",obs_list,h_data_pass)
w_pass.Import(rh_data_pass);

label = ROOT.TLatex();
label.SetTextAlign(12);
label.SetNDC();
label.SetTextSize(label.GetTextSize()*0.8);

c = ROOT.TCanvas("c","",600,600);

######################
## Z+jets modelling ##
######################

rh_zjet_pass = ROOT.RooDataHist("zjet_pass","",obs_list,h_zjet_pass)

## Relativistic Breit-Wigner
zjet_mz_pass = ROOT.RooRealVar("zjet_mz_pass","zjet_mz_pass",91.18);
zjet_gammaz_pass = ROOT.RooRealVar("zjet_gammaz_pass","zjet_gammaz_pass",2.49);
pdf_zjet_bw_pass = ROOT.RooGenericPdf("pdf_zjet_bw_pass","pdf_zjet_bw_pass","@0/(pow(@0*@0 - @1*@1,2) + @2*@2*@0*@0*@0*@0/(@1*@1))",ROOT.RooArgList(obs,zjet_mz_pass,zjet_gammaz_pass));
zjet_mz_pass.setConstant(True);
zjet_gammaz_pass.setConstant(True);

## Gaussian resolution
zjet_gmean_pass = ROOT.RooRealVar("zjet_gmean_pass","zjet_gmean_pass",0.,-20,20);
zjet_gsigmaL_pass = ROOT.RooRealVar("zjet_gsigmaL_pass","zjet_gsigmaL_pass",2.5,1,15);
zjet_gsigmaR_pass = ROOT.RooRealVar("zjet_gsigmaR_pass","zjet_gsigmaR_pass",2.5,1,15);

if args.float_mass_peak:
    CMS_jms_unc = ROOT.RooRealVar("CMS_jms_unc","CMS_jms_unc",0.,-1.,1.);
else:
    CMS_jms_unc = ROOT.RooRealVar("CMS_jms_unc","CMS_jms_unc",0.,-5.,5.);
if args.float_mass_reso:
    CMS_jmr_unc = ROOT.RooRealVar("CMS_jmr_unc","CMS_jmr_unc",0.,-1.,1.);
else:
    CMS_jmr_unc = ROOT.RooRealVar("CMS_jmr_unc","CMS_jmr_unc",0.,-5.,5.);
CMS_jms_unc.setConstant(True);
CMS_jmr_unc.setConstant(True);

zjet_jms_unc_pass = ROOT.RooRealVar("zjet_jms_unc_pass","zjet_jms_unc_pass",args.jms_uncertainty);
zjet_jmr_unc_pass = ROOT.RooRealVar("zjet_jmr_unc_pass","zjet_jmr_unc_pass",args.jmr_uncertainty);
zjet_jms_unc_pass.setConstant(True);
zjet_jmr_unc_pass.setConstant(True);

zjet_gpeak_pass = ROOT.RooFormulaVar("zjet_gpeak_pass","","@0*(1+@1*(@0+@3)*@2)",ROOT.RooArgList(zjet_gmean_pass,zjet_jms_unc_pass,CMS_jms_unc,zjet_mz_pass))
zjet_gresoL_pass = ROOT.RooFormulaVar("zjet_gresoL_pass","","@0*(1+@1*@2)",ROOT.RooArgList(zjet_gsigmaL_pass,zjet_jmr_unc_pass,CMS_jmr_unc))
zjet_gresoR_pass = ROOT.RooFormulaVar("zjet_gresoR_pass","","@0*(1+@1*@2)",ROOT.RooArgList(zjet_gsigmaR_pass,zjet_jmr_unc_pass,CMS_jmr_unc))

pdf_zjet_reso_pass = ROOT.RooBifurGauss("pdf_zjet_reso_pass","pdf_zjet_reso_pass",obs,zjet_gpeak_pass,zjet_gresoL_pass,zjet_gresoR_pass)

pdf_zjet_sig_pass = ROOT.RooFFTConvPdf("pdf_zjet_sig_pass","pdf_zjet_sig_pass",obs,pdf_zjet_bw_pass,pdf_zjet_reso_pass);
    
## combinatorial backgorund
if args.use_poly_bkg:
    zjet_coef_pass_1 = ROOT.RooRealVar("zjet_coef_pass_1","zjet_coef_pass_1",0.001,-10,10)
    zjet_coef_pass_2 = ROOT.RooRealVar("zjet_coef_pass_2","zjet_coef_pass_2",0.001,-10,10)
    pdf_zjet_bkg_pass = ROOT.RooChebychev("pdf_zjet_bkg_pass","pdf_zjet_bkg_pass",obs,ROOT.RooArgList(zjet_coef_pass_1,zjet_coef_pass_2));
else:
    zjet_coef_mean_pass = ROOT.RooRealVar("zjet_coef_mean_pass","zjet_coef_mean_pass",91.,80.,110.)
    zjet_coef_sigmaL_pass = ROOT.RooRealVar("zjet_coef_sigmaL_pass","zjet_coef_sigmaL_pass",20.,10.,50)
    zjet_coef_sigmaR_pass = ROOT.RooRealVar("zjet_coef_sigmaR_pass","zjet_coef_sigmaR_pass",20.,10.,50)
    zjet_coef_gmean_pass = ROOT.RooFormulaVar("zjet_coef_gmean_pass","","@0*(1+@1*@2)",ROOT.RooArgList(zjet_coef_mean_pass,zjet_jms_unc_pass,CMS_jms_unc))    
    zjet_coef_gsigmaL_pass = ROOT.RooFormulaVar("zjet_coef_gsigmaL_pass","","@0*(1+@1*@2)",ROOT.RooArgList(zjet_coef_sigmaL_pass,zjet_jmr_unc_pass,CMS_jmr_unc))
    zjet_coef_gsigmaR_pass = ROOT.RooFormulaVar("zjet_coef_gsigmaR_pass","","@0*(1+@1*@2)",ROOT.RooArgList(zjet_coef_sigmaR_pass,zjet_jmr_unc_pass,CMS_jmr_unc))    
    pdf_zjet_bkg_pass = ROOT.RooBifurGauss("pdf_zjet_bkg_pass","pdf_zjet_bkg_pass",obs,zjet_coef_gmean_pass,zjet_coef_gsigmaL_pass,zjet_coef_gsigmaR_pass);
    
zjet_frac_pass = ROOT.RooRealVar("zjet_frac_pass","zjet_frac_pass",0.1,0.,1.);

pdf_zjet_pass = ROOT.RooAddPdf("pdf_zjet_pass","pdf_zjet_pass",ROOT.RooArgList(pdf_zjet_sig_pass,pdf_zjet_bkg_pass),ROOT.RooArgList(zjet_frac_pass),True);
pdf_zjet_pass_norm = ROOT.RooRealVar(pdf_zjet_pass.GetName()+"_norm","",rh_zjet_pass.sumEntries())
pdf_zjet_pass_norm.setConstant(True);

fit_zjet_pass_res = pdf_zjet_pass.fitTo(rh_zjet_pass,ROOT.RooFit.Save(),ROOT.RooFit.Optimize(1),ROOT.RooFit.SumW2Error(True),ROOT.RooFit.Minimizer("Minuit2"));

h_fit_zjet_pass = pdf_zjet_pass.createHistogram("h_fit_zjet_pass",obs,ROOT.RooFit.Binning(obs.getBins()*args.rebin_pdf));
h_fit_zjet_pass.Scale(pdf_zjet_pass_norm.getVal()*args.rebin_pdf);

h_fit_zjet_bkg_pass = pdf_zjet_bkg_pass.createHistogram("h_fit_zjet_bkg_pass",obs,ROOT.RooFit.Binning(obs.getBins()*args.rebin_pdf));
h_fit_zjet_bkg_pass.Scale(pdf_zjet_pass_norm.getVal()*args.rebin_pdf*(1-zjet_frac_pass.getVal()));

h_fit_zjet_sig_pass = pdf_zjet_sig_pass.createHistogram("h_fit_zjet_sig_pass",obs,ROOT.RooFit.Binning(obs.getBins()*args.rebin_pdf));
h_fit_zjet_sig_pass.Scale(pdf_zjet_pass_norm.getVal()*args.rebin_pdf*zjet_frac_pass.getVal());

h_fit_zjet_pass_test = pdf_zjet_pass.createHistogram("h_fit_zjet_pass_test",obs);
h_fit_zjet_pass_test.Scale(pdf_zjet_pass_norm.getVal());
chi2_zjet_pass,ndf_zjet_pass = getChi2(h_zjet_pass,h_fit_zjet_pass_test);
chi2_zjet_pass = chi2_zjet_pass/(ndf_zjet_pass-fit_zjet_pass_res.floatParsFinal().getSize());
if args.cat_id == "cat0":
    max_zjet_pass, hwhm_zjet_pass = getMaxAndHWHM(h_fit_zjet_pass);
else:
    max_zjet_pass, hwhm_zjet_pass = getMaxAndHWHM(h_fit_zjet_sig_pass);
    

if args.use_poly_bkg:
    zjet_coef_pass_1.setConstant(True);
    zjet_coef_pass_2.setConstant(True);
else:
    zjet_coef_mean_pass.setConstant(True);
    zjet_coef_sigmaL_pass.setConstant(True);
    zjet_coef_sigmaR_pass.setConstant(True);
    
zjet_frac_pass.setConstant(True);
zjet_gmean_pass.setConstant(True);
zjet_gsigmaL_pass.setConstant(True);
zjet_gsigmaR_pass.setConstant(True);
CMS_jmr_unc.setConstant(False);
CMS_jms_unc.setConstant(False);

w_pass.Import(pdf_zjet_pass);
w_pass.Import(pdf_zjet_pass_norm);

h_zjet_pass.GetXaxis().SetTitle(args.mass_obs+" (GeV)");
h_zjet_pass.GetYaxis().SetTitle("Events");
h_zjet_pass.SetMarkerColor(ROOT.kBlack);
h_zjet_pass.SetLineColor(ROOT.kBlack);
h_zjet_pass.SetMarkerSize(0.6);
h_zjet_pass.SetMarkerStyle(20);
h_zjet_pass.Rebin(args.rebin_data);
h_zjet_pass.GetYaxis().SetRangeUser(0.,h_zjet_pass.GetMaximum()*1.25);
h_zjet_pass.Draw("EP");
h_fit_zjet_bkg_pass.SetLineColor(ROOT.kBlue);
h_fit_zjet_bkg_pass.SetLineWidth(2);
h_fit_zjet_bkg_pass.Scale(args.rebin_data);
if args.plot_bkg:
    h_fit_zjet_bkg_pass.Draw("hist same");
h_fit_zjet_pass.SetLineColor(ROOT.kRed);
h_fit_zjet_pass.SetLineWidth(2);
h_fit_zjet_pass.Scale(args.rebin_data);
h_fit_zjet_pass.Draw("hist same");
h_zjet_pass.Draw("EPsame");
ROOT.CMS_lumi(c,"%.1f"%(lumi_dict[args.year]),False,False,True);
label.DrawLatex(0.65,0.8,"#chi^{2}/ndf=%.2f"%(chi2_zjet_pass));
label.DrawLatex(0.65,0.75,"Peak=%.2f"%(max_zjet_pass))
label.DrawLatex(0.65,0.7,"HWHM=%.2f"%(hwhm_zjet_pass));
c.SaveAs(args.output_directory+"/zjet_pass_fit_"+args.cat_id+".png","png");
c.SaveAs(args.output_directory+"/zjet_pass_fit_"+args.cat_id+".pdf","pdf");

######################
## W+jets modelling ##
######################

rh_wjet_pass = ROOT.RooDataHist("wjet_pass","",obs_list,h_wjet_pass)

wjet_mw_pass = ROOT.RooRealVar("wjet_mw_pass","wjet_mw_pass",80.37);
wjet_gammaw_pass = ROOT.RooRealVar("wjet_gammaw_pass","wjet_gammaw_pass",2.08);
pdf_wjet_bw_pass = ROOT.RooGenericPdf("pdf_wjet_bw_pass","pdf_wjet_bw_pass","@0/(pow(@0*@0 - @1*@1,2) + @2*@2*@0*@0*@0*@0/(@1*@1))",ROOT.RooArgList(obs,wjet_mw_pass,wjet_gammaw_pass));
wjet_mw_pass.setConstant(True);
wjet_gammaw_pass.setConstant(True);

wjet_gmean_pass = ROOT.RooRealVar("wjet_gmean_pass","wjet_gmean_pass",zjet_gmean_pass.getVal(),zjet_gmean_pass.getVal()-5,zjet_gmean_pass.getVal()+5);
wjet_gsigmaL_pass = ROOT.RooRealVar("wjet_gsigmaL_pass","wjet_gsigmaL_pass",zjet_gsigmaL_pass.getVal(),zjet_gsigmaL_pass.getVal()*0.5,zjet_gsigmaL_pass.getVal()*2.);
wjet_gsigmaR_pass = ROOT.RooRealVar("wjet_gsigmaR_pass","wjet_gsigmaR_pass",zjet_gsigmaR_pass.getVal(),zjet_gsigmaR_pass.getVal()*0.5,zjet_gsigmaR_pass.getVal()*2.);
wjet_jms_unc_pass = ROOT.RooRealVar("wjet_jms_unc_pass","wjet_jms_unc_pass",args.jms_uncertainty);
wjet_jmr_unc_pass = ROOT.RooRealVar("wjet_jmr_unc_pass","wjet_jmr_unc_pass",args.jmr_uncertainty);
wjet_jms_unc_pass.setConstant(True);
wjet_jmr_unc_pass.setConstant(True);
CMS_jms_unc.setConstant(True);
CMS_jmr_unc.setConstant(True);

wjet_gpeak_pass = ROOT.RooFormulaVar("wjet_gpeak_pass","","@0*(1+@1*(@0+@3)*@2)",ROOT.RooArgList(wjet_gmean_pass,wjet_jms_unc_pass,CMS_jms_unc,wjet_mw_pass))
wjet_gresoL_pass = ROOT.RooFormulaVar("wjet_gresoL_pass","","@0*(1+@1*@2)",ROOT.RooArgList(wjet_gsigmaL_pass,wjet_jmr_unc_pass,CMS_jmr_unc))
wjet_gresoR_pass = ROOT.RooFormulaVar("wjet_gresoR_pass","","@0*(1+@1*@2)",ROOT.RooArgList(wjet_gsigmaR_pass,wjet_jmr_unc_pass,CMS_jmr_unc))

pdf_wjet_reso_pass = ROOT.RooBifurGauss("pdf_wjet_reso_pass","pdf_wjet_reso_pass",obs,wjet_gpeak_pass,wjet_gresoL_pass,wjet_gresoR_pass)

pdf_wjet_pass = ROOT.RooFFTConvPdf("pdf_wjet_pass","pdf_wjet_pass",obs,pdf_wjet_bw_pass,pdf_wjet_reso_pass);


pdf_wjet_pass_norm = ROOT.RooRealVar(pdf_wjet_pass.GetName()+"_norm","",rh_wjet_pass.sumEntries())
pdf_wjet_pass_norm.setConstant(True);

fit_wjet_pass_res = pdf_wjet_pass.fitTo(rh_wjet_pass,ROOT.RooFit.Save(),ROOT.RooFit.Optimize(1),ROOT.RooFit.SumW2Error(True),ROOT.RooFit.Minimizer("Minuit2"));

h_fit_wjet_pass = pdf_wjet_pass.createHistogram("h_fit_wjet_pass",obs,ROOT.RooFit.Binning(obs.getBins()*args.rebin_pdf));
h_fit_wjet_pass.Scale(pdf_wjet_pass_norm.getVal()*args.rebin_pdf);


h_fit_wjet_pass_test = pdf_wjet_pass.createHistogram("h_fit_wjet_pass_test",obs);
h_fit_wjet_pass_test.Scale(pdf_wjet_pass_norm.getVal());
chi2_wjet_pass,ndf_wjet_pass = getChi2(h_wjet_pass,h_fit_wjet_pass_test);
chi2_wjet_pass = chi2_wjet_pass/(ndf_wjet_pass-fit_wjet_pass_res.floatParsFinal().getSize());
max_wjet_pass, hwhm_wjet_pass = getMaxAndHWHM(h_fit_wjet_pass);

wjet_gmean_pass.setConstant(True);
wjet_gsigmaL_pass.setConstant(True);
wjet_gsigmaR_pass.setConstant(True);
CMS_jms_unc.setConstant(False);
CMS_jmr_unc.setConstant(False);
    
w_pass.Import(pdf_wjet_pass);
w_pass.Import(pdf_wjet_pass_norm);

h_wjet_pass.GetXaxis().SetTitle(args.mass_obs+" (GeV)");
h_wjet_pass.GetYaxis().SetTitle("Events");
h_wjet_pass.SetMarkerColor(ROOT.kBlack);
h_wjet_pass.SetLineColor(ROOT.kBlack);
h_wjet_pass.SetMarkerSize(0.6);
h_wjet_pass.SetMarkerStyle(20);
h_wjet_pass.Rebin(args.rebin_data);
h_wjet_pass.GetYaxis().SetRangeUser(0.,h_wjet_pass.GetMaximum()*1.25);
h_wjet_pass.Draw("EP");
h_fit_wjet_pass.SetLineColor(ROOT.kRed);
h_fit_wjet_pass.SetLineWidth(2);
h_fit_wjet_pass.Scale(args.rebin_data);
h_fit_wjet_pass.Draw("hist same");
h_wjet_pass.Draw("EPsame");
ROOT.CMS_lumi(c,"%.1f"%(lumi_dict[args.year]),False,False,True);
label.DrawLatex(0.65,0.8,"#chi^{2}/ndf=%.2f"%(chi2_wjet_pass));
label.DrawLatex(0.65,0.75,"Peak=%.2f"%(max_wjet_pass))
label.DrawLatex(0.65,0.7,"HWHM=%.2f"%(hwhm_wjet_pass));
c.SaveAs(args.output_directory+"/wjet_pass_fit_"+args.cat_id+".png","png");
c.SaveAs(args.output_directory+"/wjet_pass_fit_"+args.cat_id+".pdf","pdf");

######################
## QCD MC modelling ##
######################

rh_qcd_pass = ROOT.RooDataHist("qcd_pass","",obs_list,h_qcd_pass)

## order tune in MC
qcd_coef_pass_1 = ROOT.RooRealVar("qcd_coef_pass_1","qcd_coef_pass_1",0.001,-10,10)
qcd_coef_pass_2 = ROOT.RooRealVar("qcd_coef_pass_2","qcd_coef_pass_2",0.001,-10,10)
qcd_coef_pass_3 = ROOT.RooRealVar("qcd_coef_pass_3","qcd_coef_pass_3",0.001,-10,10)
qcd_coef_pass_4 = ROOT.RooRealVar("qcd_coef_pass_4","qcd_coef_pass_4",0.001,-10,10)


#if args.tagger == "pnet" and args.cat_id == "cat3":
#    pdf_qcd_pass = ROOT.RooChebychev("pdf_qcd_pass","",obs,ROOT.RooArgList(qcd_coef_pass_1,qcd_coef_pass_2,qcd_coef_pass_3,qcd_coef_pass_4));
#else:
#    pdf_qcd_pass = ROOT.RooChebychev("pdf_qcd_pass","",obs,ROOT.RooArgList(qcd_coef_pass_1,qcd_coef_pass_2,qcd_coef_pass_3));
pdf_qcd_pass = ROOT.RooChebychev("pdf_qcd_pass","",obs,ROOT.RooArgList(qcd_coef_pass_1,qcd_coef_pass_2,qcd_coef_pass_3));

fit_qcd_pass_res = pdf_qcd_pass.fitTo(rh_qcd_pass,ROOT.RooFit.Save(),ROOT.RooFit.Optimize(1),ROOT.RooFit.SumW2Error(True),ROOT.RooFit.Minimizer("Minuit2"));

pdf_qcd_pass_norm = ROOT.RooRealVar(pdf_qcd_pass.GetName()+"_norm","",h_qcd_pass.Integral(),0.5*h_qcd_pass.Integral(),2.0*h_qcd_pass.Integral())
pdf_qcd_pass_norm.setConstant(False);

h_fit_qcd_pass = pdf_qcd_pass.createHistogram("h_fit_qcd_pass",obs,ROOT.RooFit.Binning(obs.getBins()*args.rebin_pdf));
h_fit_qcd_pass.Scale(pdf_qcd_pass_norm.getVal()*args.rebin_pdf);

w_pass.Import(pdf_qcd_pass);

h_fit_qcd_pass_test = pdf_qcd_pass.createHistogram("h_fit_qcd_pass_test",obs);
h_fit_qcd_pass_test.Scale(pdf_qcd_pass_norm.getVal());
chi2_qcd_pass,ndf_qcd_pass = getChi2(h_qcd_pass,h_fit_qcd_pass_test);
chi2_qcd_pass = chi2_qcd_pass/(ndf_qcd_pass-fit_qcd_pass_res.floatParsFinal().getSize());


h_qcd_pass.GetXaxis().SetTitle(args.mass_obs+" (GeV)");
h_qcd_pass.GetYaxis().SetTitle("Events");
h_qcd_pass.SetMarkerColor(ROOT.kBlack);
h_qcd_pass.SetLineColor(ROOT.kBlack);
h_qcd_pass.SetMarkerSize(0.6);
h_qcd_pass.SetMarkerStyle(20);
h_qcd_pass.Rebin(args.rebin_data);
h_qcd_pass.GetYaxis().SetRangeUser(0.,h_qcd_pass.GetMaximum()*1.25);
h_qcd_pass.Draw("EP");
h_fit_qcd_pass.SetLineColor(ROOT.kRed);
h_fit_qcd_pass.SetLineWidth(2);
h_fit_qcd_pass.Scale(args.rebin_data);
h_fit_qcd_pass.Draw("hist same");
h_qcd_pass.Draw("EPsame");

ROOT.CMS_lumi(c,"%.1f"%(lumi_dict[args.year]),False,False,True);
label.DrawLatex(0.65,0.8,"#chi^{2}/ndf=%.2f"%(chi2_qcd_pass));
c.SaveAs(args.output_directory+"/qcd_pass_fit_"+args.cat_id+".png","png");
c.SaveAs(args.output_directory+"/qcd_pass_fit_"+args.cat_id+".pdf","pdf");

#### prefit distributions
pdf_qcd_pass_norm.setVal(rh_data_pass.sumEntries()-pdf_wjet_pass_norm.getVal()-pdf_zjet_pass_norm.getVal());
w_pass.Import(pdf_qcd_pass_norm);
h_fit_qcd_pass.Scale(pdf_qcd_pass_norm.getVal()*args.rebin_pdf/h_fit_qcd_pass.Integral())

### Save output files
f_out_pass = ROOT.TFile("workspace/workspace_"+args.cat_id+"_pass.root","RECREATE");
f_out_pass.cd()
w_pass.Write("w");
f_out_pass.Close();

### write datacard
os.chdir("workspace");
h_zjet_ewk_pass = f_zjet.Get("hist_ak8_"+args.mass_obs+"_ewk");
h_wjet_ewk_pass = f_wjet.Get("hist_ak8_"+args.mass_obs+"_ewk");

sys_pass = {"NLOEWK_corr_zjet": 0.5*((h_zjet_ewk_pass.Integral()+h_zjet_pass.Integral())/h_zjet_pass.Integral()), "NLOEWK_corr_wjet": 0.5*((h_wjet_ewk_pass.Integral()+h_wjet_pass.Integral())/h_wjet_pass.Integral())}
dc_pass = createCardTemplate(args.cat_id,"pass","workspace_"+args.cat_id+"_pass.root",sys_pass,"w");
