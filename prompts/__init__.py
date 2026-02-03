'''
This package contains the prompts for a specific book format.
For ex. Class 10th maths, Class 9th maths and Class 8th maths
share the same book format.
So a single prompt is used for all of them.
The prompts tells to the agent how to decomposen a chapter of this book into 
concepts and topics.
'''

#from prompts.class10_maths import NCERT_CLASS_10_Maths
from prompts.class10_maths import NCERT_GEN

__all__ = [
   # "NCERT_CLASS_10_Maths",
    "NCERT_GEN"
]
