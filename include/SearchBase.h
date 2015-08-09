#ifndef ___SearchBase
#define ___SearchBase

#include "ManagerBase.h"
#include "VBMManager.h"
#include "SBMManager.h"

class SearchBase {
    friend class SearchFactory;
    protected:
    SearchBase();	// called by subclasses only
    public:
    virtual ~SearchBase();

    virtual Model **search(Model *start);
    bool isDirected() { return directed; }
    bool makeProjection() { return projection; }
    ManagerBase *getManager() { return manager; }

    protected:
    void setManager(ManagerBase *mgr) { manager = mgr; }
    void setDirected(bool dir) { directed = dir; }
    void setMakeProjection(bool proj) { projection = proj; }

    //-- data
    ManagerBase *manager;
    bool directed;	// system is directed (has dependent variables)
    bool projection; // create a projection table for all new relations
};

class SearchFactory {
    public:
	static SearchBase *getSearchMethod(ManagerBase *manager, const char *name, bool proj = true);
};

#endif
