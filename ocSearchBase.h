/*
 * ocSearchBase.h -- base class for search algorithms. Each search step takes a single
 * model as a starting point, and returns a list of models. Some subclasses may have
 * control attributes which affect searches.
 */
 
#ifndef OCSEARCHBASE_H
#define OCSEARCHBASE_H

#include "ocCore.h"
#include "ocManagerBase.h"
#include "ocVBMManager.h"
#include "ocSBMManager.h"

class ocSearchBase {
    friend class ocSearchFactory;
    protected:
    ocSearchBase();	// called by subclasses only
    public:
    virtual ~ocSearchBase();

    virtual ocModel **search(ocModel *start);
    bool isDirected() { return directed; }
    bool makeProjection() { return projection; }
    ocManagerBase *getManager() { return manager; }

    protected:
    void setManager(ocManagerBase *mgr) { manager = mgr; }
    void setDirected(bool dir) { directed = dir; }
    void setMakeProjection(bool proj) { projection = proj; }

    //-- data
    ocManagerBase *manager;
    bool directed;	// system is directed (has dependent variables)
    bool projection; // create a projection table for all new relations
};

class ocSearchFactory {
    public:
	static ocSearchBase *getSearchMethod(ocManagerBase *manager, const char *name, bool proj = true);
};

#endif
