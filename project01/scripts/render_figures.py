"""Publication style wrapper around the frozen notebook03 plotting functions."""
from pathlib import Path
import os
import sys
PROJECT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(PROJECT/'artifacts/plot_style')
sys.path.insert(0,str(PROJECT/'web/backend'))
from project01_core.evaluation import plot_results,read_results
if __name__=='__main__':
    plot_results(read_results(PROJECT/'artifacts/phase2/evaluation/results'),PROJECT/'report/figures')
    print('Rendered saved-results plots with notebook03 functions and publication style; no inference')
