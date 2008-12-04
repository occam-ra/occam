/*
 * ocSearchBase.cpp - implements search base class
 */
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "ocSearchBase.h"
#include "ocSearch.h"

struct ocSearchType {
	const char *name;
	ocSearchBase * (*make)();
};

ocSearchType searchTypes[] = {
	{ "full-down", ocSearchFullDown::make },
	{ "full-up", ocSearchFullUp::make },
	{ "loopless-down", ocSearchLooplessDown::make },
	{ "loopless-up", ocSearchLooplessUp::make },
	{ "disjoint-up", ocSearchDisjointUp::make },
	{ "chain-up", ocSearchChain::make },
};

ocSearchBase::ocSearchBase(): manager(0), directed(false)
{
}

ocSearchBase::~ocSearchBase()
{
}

ocModel **ocSearchBase::search(ocModel *start)
{
	return NULL;	// should never be called
}

ocSearchBase* ocSearchFactory::getSearchMethod(ocVBMManager *mgr, const char *name, bool proj)
{
	ocSearchBase *search = NULL;
	ocSearchType *type;
	
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


