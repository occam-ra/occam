/*
 * ocSearch.h - contains basic search algorithms for the LM
 */

#include "ocSearchBase.h"

class ocSearchFullDown : public ocSearchBase {
    public:
	ocSearchFullDown() {};
	virtual ~ocSearchFullDown() {};
	ocModel **search(ocModel *start);
	static ocSearchBase *make() { return new ocSearchFullDown(); }
};

class ocSearchFullUp : public ocSearchBase {
    public:
	ocSearchFullUp(): parentList(0), parentListCount(0), parentListMax(0) {};
	virtual ~ocSearchFullUp() {};
	ocModel **search(ocModel *start);
	void makeCandidate(struct SearchStackEntry *stack, int top, ocModel *start);
	static ocSearchBase *make() { return new ocSearchFullUp(); }

    protected:
	ocModel **parentList;
	long parentListCount;
	long parentListMax;
};

class ocSearchLooplessDown : public ocSearchBase {
    public:
	ocSearchLooplessDown() {};
	virtual ~ocSearchLooplessDown() {};
	ocModel **search(ocModel *start);
	static ocSearchBase *make() { return new ocSearchLooplessDown(); }

};

class ocSearchLooplessUp : public ocSearchBase {
    public:
	ocSearchLooplessUp() {};
	virtual ~ocSearchLooplessUp() {};
	ocModel **search(ocModel *start);
	static ocSearchBase *make() { return new ocSearchLooplessUp(); }

};

class ocSearchDisjointUp : public ocSearchBase {
    public:
	ocSearchDisjointUp() {};
	virtual ~ocSearchDisjointUp() {};
	ocModel **search(ocModel *start);
	static ocSearchBase *make() { return new ocSearchDisjointUp(); }

};

class ocSearchDisjointDown : public ocSearchBase {
    public:
	ocModel **search(ocModel *start);
	static ocSearchBase *make() { return new ocSearchDisjointDown();}
};

class ocSearchChain : public ocSearchBase {
    public:
	ocSearchChain() {};
	virtual ~ocSearchChain() {};
	ocModel **search(ocModel *start);
	static ocSearchBase *make() { return new ocSearchChain(); }
    protected:
	bool makeChainModels();
	int varCount;	// variables in model
	int slot;		// next position in models
	int maxChildren; //size of models array, precomputed
	ocModel **models; // place to put generated models
	int *varStack; // stack of variables for recursion
	int stackPtr;	// current position in varStack
	int depVar;		// index of the dependent variable, -1 for neutral systems
	ocRelation *indOnlyRel; // index of IV relation, -1 for neutral systems
	bool isDirected;
};
