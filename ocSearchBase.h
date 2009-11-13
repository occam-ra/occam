/*
 * ocSearchBase.h -- base class for search algorithms. Each search step takes a single
 * model as a starting point, and returns a list of models. Some subclasses may have
 * control attributes which affect searches.
 */
 
#ifndef OCSEARCHBASE_H
#define OCSEARCHBASE_H

#include "ocCore.h"
#include "ocVBMManager.h"

class ocSearchBase {
    friend class ocSearchFactory;
    protected:
    ocSearchBase();	// called by subclasses only
    public:
    virtual ~ocSearchBase();

    virtual ocModel **search(ocModel *start);
    bool isDirected() { return directed; }
    bool makeProjection() { return projection; }
    ocVBMManager *getManager() { return manager; }

    protected:
    void setManager(ocVBMManager *mgr) { manager = mgr; }
    void setDirected(bool dir) { directed = dir; }
    void setMakeProjection(bool proj) { projection = proj; }

    //-- data
    ocVBMManager *manager;
    bool directed;	// system is directed (has dependent variables)
    bool projection; // create a projection table for all new relations
};

class ocSearchFactory {
    public:
	static ocSearchBase *getSearchMethod(ocVBMManager *manager, const char *name, bool proj = true);
};

#endif
