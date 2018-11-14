/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#ifndef ___Search
#define ___Search
#include "SearchBase.h"

class SearchFullDown : public SearchBase {
    public:
	SearchFullDown() {};
	virtual ~SearchFullDown() {};
	Model **search(Model *start);
	static SearchBase *make() { return new SearchFullDown(); }
};

class SearchFullUp : public SearchBase {
    public:
	SearchFullUp(): parentList(0), parentListCount(0), parentListMax(0) {};
	virtual ~SearchFullUp() {};
	Model **search(Model *start);
	void makeCandidate(class SearchStackEntry *stack, int top, Model *start);
	static SearchBase *make() { return new SearchFullUp(); }

    protected:
	Model **parentList;
	long parentListCount;
	long parentListMax;
};

class SearchLooplessDown : public SearchBase {
    public:
	SearchLooplessDown() {};
	virtual ~SearchLooplessDown() {};
	Model **search(Model *start);
	static SearchBase *make() { return new SearchLooplessDown(); }
};

class SearchSbFullUp : public SearchBase {
    public:
	SearchSbFullUp() {};
	virtual ~SearchSbFullUp() {};
	Model **search(Model *start);
	static SearchBase *make() { return new SearchSbFullUp(); }
    void recurseDirected(Model *start, int cur_var, int cur_index, int *var_indices, int *state_indices, int &models_found, Model **model_list);
    bool addToCache(Model *model, int &models_found, Model **model_list);
};

class SearchSbLooplessUp : public SearchBase {
    public:
	SearchSbLooplessUp() {};
	virtual ~SearchSbLooplessUp() {};
	Model **search(Model *start);
	static SearchBase *make() { return new SearchSbLooplessUp(); }
    void recurseDirected(int cur_var, int cur_index, int *var_indices, int *state_indices, int &models_found, Model **model_list);
    bool addToCache(Model *model, int &models_found, Model **model_list);
};

class SearchLooplessUp : public SearchBase {
    public:
	SearchLooplessUp() {};
	virtual ~SearchLooplessUp() {};
	Model **search(Model *start);
	static SearchBase *make() { return new SearchLooplessUp(); }
};

class SearchDisjointUp : public SearchBase {
    public:
	SearchDisjointUp() {};
	virtual ~SearchDisjointUp() {};
	Model **search(Model *start);
	static SearchBase *make() { return new SearchDisjointUp(); }
};

class SearchDisjointDown : public SearchBase {
    public:
	Model **search(Model *start);
	static SearchBase *make() { return new SearchDisjointDown();}
};

class SearchChain : public SearchBase {
    public:
	SearchChain() {};
	virtual ~SearchChain() {};
	Model **search(Model *start);
	static SearchBase *make() { return new SearchChain(); }
    protected:
	bool makeChainModels();
	int varCount;	// variables in model
	int slot;		// next position in models
	int maxChildren; //size of models array, precomputed
	Model **models; // place to put generated models
	int *varStack; // stack of variables for recursion
	int stackPtr;	// current position in varStack
	int depVar;		// index of the dependent variable, -1 for neutral systems
	Relation *indOnlyRel; // index of IV relation, -1 for neutral systems
	bool isDirected;
};

#endif
