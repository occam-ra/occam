## OCCAM Application Structure

### Overview of existing design

The current structure of OCCAM appears to date to about 2000 (see the Design Proposal document which contains references to some of the existing core classes). The application design and implementation is not well-documented. This document reflects an initial attempt at providing some transparency on the OCCAM structure, and helping developers new to the project (capstone team members or others) to get oriented without having to spend an excessive amount of time digging through the code (though this document cannot substitute for spending time with the code).

OCCAM consists of a core of functionality, implemented in custom C++ classes, which is wrapped in Python (apparently using SWIG - details from Joe?). The python wrapper consists primarily of ocUtils, a very lightweight helper class which mostly passes parameters to the C++ objects which perform nearly all of the RA computation and generate some/most (though not all) of the output. In some places there is high-level logic (though almost no actual RA computation) handled by python functions - see, for example, doFit() at ocutils.py(684).

(UML diagram of structure)
 
This core of functionality can be accessed by two methods: command line (CL) or web interfaces. The command-line files (at install/cl/) are functional, and provide essentially the same output as the web version (without the HTML). The small existing OCCAM user base uses the web version almost exclusively. The CL files are useful for debugging/tracing or otherwise inspecting the behavior of the application, but are not in current use. The web interface, though dated, provides a reasonably good level of functionality (load data; search; fit; examine variable states, predictions, and statistical and info-theoretic measures) for the researchers currently using OCCAM.

The core functionality is reliable and rationally implemented. Implementation in C++ allows computation to be performed very quickly - OCCAM can quickly search a very large space of variables and states, and fit a model once it is selected from search results. Speed is the primary motivation for this application structure (C++ extensions to python). There are some scattered issues (for example with memory management in the state-based part of OCCAM), but overall the essential RA methods are well-implemented.It is important, in developing OCCAM, that this core functionality be preserved in its current form. There is no need, at least in the short term, to redo any significant parts of the RA computation (though the code will definitely need some cleanup and separation of the core functions from the input/output and other components best handled by the user or application programmer).

What is needed, is a reworking of the python layer (which handles high-level workflow), the user interface, and 

After many years of proprietary development, it is time to update the approach to developing OCCAM to incorporate open-source practices and ideals, modern paradigms of design and implementation, best-available tools, and a structure which will be easier to update and maintain.

  

(Find an existing project - and maybe even a design specification - that uses python/c++ in a similar way as an example of what we want this to look like).

Output:

Example of output generated directly in C++: ![](https://lh6.googleusercontent.com/-BAwk6w6B0CVzG4vziOIWBE4OWTPrw1DhfT3CFM2QSW3GjIJPOU28HCqwSy79ihpooshz-Y8-Qt_dbz_Zpp4JBZwnlNJNjOjrEuXFj39acWoELFiJsvDMS5PtuCOrKM5xqL3-K44)

  
Data handling (file format and otherwise): input data formatting is, in my view, perhaps the biggest obstacle to OCCAM adoption. OCCAM has finally been open-sourced, but it has for years been available in the (proprietary) web format. The current software world moves at the speed of light - someone can install packages with pip or similar tools, combine multiple python libraries, extend python with C++ or other languages, and build a powerful application in a matter of days or hours. Being forced to use a proprietary data format for which we do not have good conversion tools is a major barrier to using OCCAM.

There are many existing data formats which should be suitable for OCCAM, and which can be manipulated using functionality from the python standard library or other packages such as pandas. The

Caching results (reports): OCCAM employs a hash-based caching mechanism

> Written with [StackEdit](https://stackedit.io/).
<!--stackedit_data:
eyJoaXN0b3J5IjpbMTYxMjA4NDcwNSwtOTkwOTM1OTEsLTE2Mj
U5NjE5NDJdfQ==
-->