#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "SearchBase.h"
#include "Search.h"

struct SearchType {
    const char *name;
    SearchBase * (*make)();
};

SearchType searchTypes[] = {
    { "full-down", SearchFullDown::make },
    { "full-up", SearchFullUp::make },
    { "loopless-down", SearchLooplessDown::make },
    { "loopless-up", SearchLooplessUp::make },
    { "disjoint-up", SearchDisjointUp::make },
    { "chain-up", SearchChain::make },
    { "disjoint-down",SearchDisjointDown::make },
    { "sb-loopless-up", SearchSbLooplessUp::make },
    { "sb-full-up", SearchSbFullUp::make },
};


SearchBase::SearchBase(): manager(0), directed(false)
{
}


SearchBase::~SearchBase()
{
}


Model **SearchBase::search(Model *start)
{
    return NULL;	// should never be called
}


SearchBase* SearchFactory::getSearchMethod(ManagerBase *mgr, const char *name, bool proj)
{
    SearchBase *search = NULL;
    SearchType *type;

    //-- Find the requested search type
    for (type = searchTypes; type->name; type++) {
        if (strcmp(type->name, name) == 0) {
            search = (*type->make)();
            break;
        }
    }

    //-- If a search type was found, set its context
    if (search) {
        search->setDirected(mgr->getVariableList()->isDirected());
        search->setMakeProjection(proj);
        search->setManager(mgr);
    }
    return search;
}


