"""
DeepTrace ELA
An open-source, NIST-grade Error Level Analysis (ELA) and JPEG compression artifact forensics toolkit.
Developed by Shaheer Ul Hassan (https://shaheerulhassan.com/).
"""

from deeptrace_ela.core import AnomalyBox, ELAResult, analyze_ela

__version__ = "0.1.3"
__author__ = "Shaheer Ul Hassan"
__author_email__ = "samjanjua6@gmail.com"
__homepage__ = "https://shaheerulhassan.com/"

__all__ = ["analyze_ela", "ELAResult", "AnomalyBox", "__version__"]
