## OCCAM Application Structure

### Overview of existing design

The current structure of OCCAM appears to date to about 2000 (see the Design Proposal document which contains references to some of the existing core classes). The application design and implementation is not well-documented. This document reflects an initial attempt at providing some transparency on the OCCAM structure, and helping developers new to the project (capstone team members or others) to get oriented without having to spend an excessive amount of time digging through the code (though there's no perfect substitute for spending time with the code). 

To some extent the discussion of design and implementation issues cannot happen without reference to the code. But it should be possible to understand and discuss these issues without intimate code familiarity. This design overview attempts to provide a helpful view of the current application structure, and approaches to updating it, that can be understood by non-programmers. At the same time, it provides code-specific details which help elucidate the design issues, and will help coding contributors to get oriented.

OCCAM consists of a core of functionality, implemented in custom C++ classes, which is wrapped in Python (apparently using SWIG, a package which automatically generates the code needed for the wrapping, saving laborious hand-coding of API function calls). The python wrapper consists primarily of ocUtils, a very lightweight helper class which mostly passes parameters to the C++ objects which perform nearly all of the RA computation and generate some/most (though not all) of the output. In some places there is high-level logic (though almost no actual RA computation) handled by python functions - see below under "Python Wrapping" for an example.

![(UML diagram)](https://www.guydcutting.com/images/OCCAM-structure.png)

This core of functionality can be accessed by two methods: command line (CL) or web interfaces. The command-line files (at install/cl/) are functional, and provide essentially the same output as the web version (without the HTML). The small existing OCCAM user base uses the web version almost exclusively. The CL files are useful for debugging/tracing or otherwise inspecting the behavior of the application, but are not in current use. The web interface, though dated, provides a reasonably good level of functionality (load data; search; fit; examine variable states, predictions, and statistical and info-theoretic measures) for the researchers currently using OCCAM.

The application was designed at a time when web applications were a new frontier, and most of the more modern infrastructure of tools, packages, UIs did not exist. After many years of proprietary development, it is time to update the approach to developing OCCAM to incorporate open-source practices and ideals, modern paradigms of design and implementation, and best available tools, into a structure which will be easier to update and maintain.

### Method (RA) vs. Application (OCCAM)
One way to think about the big picture of design issues is to distinguish between the RA method and the application which implements it. RA provides a number of conceptual tools and practical procedures for analyzing data - that conceptual and practical content can be separated from the implementation - the data handling (I/O), user interface, etc. We are very lucky to have the core RA functionality largely built already (thanks Ken, Heather, Joe, and others!).

This conceptual distinction has important practical consequences. Publishing OCCAM as a python package should give the package user (who might just be using a couple of RA functions in a small notebook, or could be incorporating RA functionality into a much larger application) to core functionality while not enforcing any single way of accessing it (as the implementation currently does). Packaging OCCAM in a modular way will allow users/developers to use that functionality in whatever way works best for them.

#### Core Functionality (C++)
The core functionality is reliable and rationally implemented. Implementation in C++ allows computation to be performed very quickly - OCCAM can quickly search a very large space of variables and states, and fit a model once it is selected from search results. Balancing speed (c++) with flexibility/productivity (python) is the primary motivation for this application structure (C++ extensions to python). This guide gives a good overview of the paradigm of extending python with c++: .

[Extending C/C++ with Python](https://medium.com/practo-engineering/execute-python-code-at-the-speed-of-c-extending-python-93e081b53f04)

ThisThere are some scattered issues (for example with memory management in the state-based part of OCCAM), but overall the essential RA methods are well-implemented. It is important, in developing OCCAM, that this core functionality be preserved in its current form. There is no need, at least in the short term, to redo any significant parts of the RA computation (though the code will definitely need some cleanup and separation of the core functions from the input/output and other components best handled by the user or application programmer).

What is that core functionality (brief overview of workflow/functions)?

#### Python Wrapping
One of the most important structural improvements is, in my view, a partial reworking of the python layer (which handles high-level workflow). This change will touch on nearly every aspect of the updated application, because the design of the extension structure will underlay nearly every other element of the implementation (data handling, UI, integration, etc.). Other improvements, such as the user interface, input/output handling, etc., will follow naturally from that update. The current python layer is very thin, meaning that only a very small of computation is actually being handled by this layer. The python functionality falls into two categories: very high-level workflow, and helpers for c++ objects. Here's an example showing both some very high level workflow, and the use of ocUtils to pass parameters to the c++ objects through the manager:

![High-level logic in python](images/occam-python-logic.png)


#### User Interface
(Find an existing project - and maybe even a design specification - that uses python/c++ in a similar way as an example of what we want this to look like).

## Most Needed Updates

### Python Layer
This is in many ways the most important place to focus in the coming weeks and months. The interface between Python/C++, the functionality exposed to the python layer, and the improvements needed to make OCCAM a modern python package that makes RA functionality easy for any Python user to access in a modular and expressive way, are a primary priority in an updated approach to developing OCCAM.

### Output
Example of output generated directly in C++: [OCCAM output in c++](https://www.guydcutting.com/images/occam-cpp-output.png)

### Input (file format and otherwise)
Input data formatting is, in my view, perhaps the biggest obstacle to OCCAM adoption. OCCAM has finally been open-sourced (or the process begun anyway), but it has for years been available in the (proprietary) web format. The current software world moves at the speed of light - someone can install packages with pip or similar tools, combine multiple python libraries, extend python with C++ or other languages, and build a powerful application in a matter of days or hours. Being forced to use a proprietary data format for which we do not have good conversion tools is a major barrier to using OCCAM.

There are many existing data formats which should be suitable for OCCAM, and which can be manipulated using functionality from the python standard library or other packages such as pandas. The

### Caching results (reports and session handling) 
OCCAM employs a hash-based caching mechanism

(references)
