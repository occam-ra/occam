/*
 * Search.cpp - implements basic LM searches
 */

#include "unistd.h"
#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <memory.h>
#include "Search.h"
#include "ModelCache.h"
#include "_Core.h"
#include "Math.h"
#include <assert.h>
#include <iostream>
using namespace std;

//----- Full search down through the lattice -----

Model **SearchFullDown::search(Model *start) {
    //-- worst case - need a list with a slot for each relation in start model,
    //-- plus one for null termination of list
    int relcount = start->getRelationCount();
    Model **models = new Model *[relcount + 1];
    Model *model;
    int i, slot;
    memset(models, 0, (relcount + 1) * sizeof(Model*));
    for (i = 0, slot = 0; i < relcount; i++) {
        Relation *rel = start->getRelation(i);
        //-- skip trivial relations
        if (rel->getVariableCount() == 1)
            continue;

        //-- for directed systems, skip any relations which only have independent vars
        if (isDirected() && rel->isIndependentOnly())
            continue;

        //-- otherwise this will generate a child relation
        model = ((VBMManager *) manager)->makeChildModel(start, i, 0, makeProjection());
        if (((VBMManager *) manager)->applyFilter(model))
            models[slot++] = model;
    }
    return models;
}

//----- Full search up through the lattice -----
/*
 * This implements full upward search from a given starting model. What must be
 * found is all sets of variables v in V, with a corresponding relation r in M for each
 * variable, so that (1) v is not in r; (2) for all other r in R, v is in r; and
 * (3) the relation formed from V is not in M. For each such set, adding the relation
 * formed by V yields a parent.
 *
 * The algorithm implements a stack-based search through the list of relations,
 * finding maximal variable sets satisfying (1) and (2). When one is found, it is
 * tested against (3).
 *
 * Each stack entry contains a relation and a list of variables, along with some
 * position information about where we are in the search. The stack is initialized
 * with R0 = a relation in M, and V0 a list of all variables not in R0. A variable in V0
 * is chosen. The next stack entry is constructed by finding a new relation containing
 * the selected variable; the R1 is set to the intersection of the new relation and R0,
 * and V1 is set to all variables in R0 and not in R1. This stack building continues
 * until Rn is empty; then the set of selected variables is a candidate relation to add.
 *
 * This process is repeated for (a) all relations following the given starting relation,
 * and (b) for all variables in each variable set. If at any point no additional relations
 * can be found which need the criteria for addition to the stack, no candidate relation
 * is produced.
 */

struct SearchStackEntry {
        int relIndex; // index of the next relation to consider, among the relations in the starting model
        int nextRelIndex; // the next index to check
        int varIndex; // index of the current variable in varList
        int *innerList; // list of variable indices in all stack entries so far
        int *outerList; // list of all variable indices in all relations but this one
        int innerListCount;
        int outerListCount;

        // trivial constructor, for array allocation
        SearchStackEntry() :
                relIndex(-1), nextRelIndex(-1), varIndex(-1), innerList(0), outerList(0), innerListCount(0), outerListCount(
                        0) {
        }
        ;

        // destructor
        ~SearchStackEntry() {
            delete[] innerList;
            delete[] outerList;
        }

        // assignment
        void set(int relIndex, int varIndex, int *innerList, int innerListCount, int *outerList, int outerListCount) {
            this->relIndex = relIndex;
            this->nextRelIndex = relIndex + 1;
            this->varIndex = varIndex;
            this->innerListCount = innerListCount;
            this->outerListCount = outerListCount;
            if (this->innerList)
                delete[] this->innerList;
            this->innerList = innerList;
            if (this->outerList)
                delete[] this->outerList;
            this->outerList = outerList;
        }

        void clean() {
            if (innerList)
                delete[] innerList;
            this->innerList = NULL;
            if (outerList)
                delete[] outerList;
            this->outerList = NULL;
        }

        void dump(Model *model);
};

void SearchStackEntry::dump(Model *model) {
    char name[1000];
    VariableList *varlist = model->getRelation(0)->getVariableList();
    varlist->getPrintName(name, 1000, innerListCount, innerList);
    varlist->getPrintName(name, 1000, outerListCount, outerList);
}

//-- construct the complement variable list for a given list
static void getComplement(int *innerList, int innerListCount, int *outerList, int maxcount) {
    int here = 0;
    int *outp = outerList;
    int index;
    //-- note: this code assumes innerList is sorted
    for (int i = 0; i < maxcount; i++) {
        while (here < innerListCount && (index = innerList[here]) < i) {
            here++;
        }
        if (i != index) {
            *(outp++) = i;
        }
        //assert(outp - outerList <= maxcount - innerListCount);
    }
    //assert(outp - outerList == maxcount - innerListCount);
}

//-- check the given variable list to see if it is a subset of the given relation
bool varSubset(int *vars, int varcount, Relation *rel) {
    int i, j;
    int relvarcount = rel->getVariableCount();
    int *relvars = rel->getVariables();
    for (i = 0; i < varcount; i++) {
        for (j = 0; j < relvarcount; j++) {
            if (vars[i] == relvars[j])
                break;
        }
        //-- if got to the end of the list, no match
        if (j >= relvarcount)
            return false;
    }
    return true;
}

//-- build a list of the current variables for each stack entry
void currentVars(int *vars, SearchStackEntry *stack, int top) {
    SearchStackEntry *stackEntry;
    for (int i = 0; i < top; i++) {
        stackEntry = &stack[i];
        vars[i] = stackEntry->outerList[stackEntry->varIndex];
    }
}

//-- construct starting stack entry. Returns false on error
static bool pushStartingRelation(SearchStackEntry *stack, int &top, Model *model, int relIndex) {
    top = 0;
    Relation *rel = model->getRelation(relIndex);
    int maxcount = rel->getVariableList()->getVarCount(); // full var list size
    int varcount = rel->getVariableCount(); // size in this rel
    if (varcount == maxcount)
        return false; // must be top relation
    int *innerList = new int[varcount];
    rel->copyVariables(innerList, varcount);
    int *outerList = new int[maxcount - varcount];
    getComplement(rel->getVariables(), rel->getVariableCount(), outerList, maxcount);
    stack[top].set(relIndex, 0, innerList, varcount, outerList, maxcount - varcount);
    top++;
    return true;
}

//-- This function splits all the variables in the top of the stack, according to
//-- whether they are in the given relation or not. Those which are in go in the
//-- inner list, the rest go into the outer list.
static void splitVariables(int *relvars, int relvarcount, int *topvars, int topvarcount, int **innerList,
        int *innerListCount, int **outerList, int *outerListCount) {
    //-- rather than figuring the list sizes exactly, we'll pick an upper bound
    //-- for storage allocation
    int alloc = topvarcount;
    int *ilist, *olist, icount, ocount;
    ilist = new int[alloc];
    olist = new int[alloc];
    icount = 0;
    ocount = 0;
    //-- note: this code assumes the variables are sorted
    int index = 0;
    int here = 0;
    for (int i = 0; i < topvarcount; i++) {
        int topindex = topvars[i];
        while (here < relvarcount && (index = relvars[here]) < topindex) {
            here++;
        }
        if (index == topindex)
            ilist[icount++] = topindex;
        else
            olist[ocount++] = topindex;
    }
    *innerList = ilist;
    *outerList = olist;
    *innerListCount = icount;
    *outerListCount = ocount;
}

//-- construct stack entry. not at the bottom. The inner list contains the
//-- intersection of this relation's list and the next entry on the stack.
//-- the outer list contains all variables in the next stack entry but not in this relation
static bool pushRelation(SearchStackEntry *stack, int &top, Model *model, int relIndex) {
    //-- if stack is empty, do special initialization
    if (top == 0)
        return pushStartingRelation(stack, top, model, relIndex);

    Relation *rel = model->getRelation(relIndex);
    int maxcount = rel->getVariableList()->getVarCount(); // full var list size
    int varcount = rel->getVariableCount(); // size in this rel
    int *innerList, *outerList;
    int innerListCount, outerListCount;
    SearchStackEntry *topEntry = &stack[top - 1];
    splitVariables(rel->getVariables(), varcount, topEntry->innerList, topEntry->innerListCount, &innerList,
            &innerListCount, &outerList, &outerListCount);
    stack[top].set(relIndex, 0, innerList, innerListCount, outerList, outerListCount);
    top++;
    return true;
}

//-- Given the top of the stack, find a relation which contains all variables for
//-- entries on the stack. The search goes through all models later in the list, and
//-- all variables in the outerList
static bool pushMatchingRelation(SearchStackEntry *stack, int &top, Model *model) {
    //-- create a list of all variables in the stack
    int varcount = top;
    SearchStackEntry *stackEntry;
    int *vars = new int[top];

    //-- find a relation containing these variables
    stackEntry = &stack[top - 1];
    currentVars(vars, stack, top);
    for (; stackEntry->nextRelIndex < model->getRelationCount(); stackEntry->nextRelIndex++) {
        if (varSubset(vars, varcount, model->getRelation(stackEntry->nextRelIndex))) {
            pushRelation(stack, top, model, stackEntry->nextRelIndex);
            stackEntry->nextRelIndex++;
            delete[] vars;
            return true;
        }
    }
    //-- no further candidates found
    delete[] vars;
    return false;
}

static bool pop(SearchStackEntry *stack, int &top) {
    if (top <= 0)
        return false;
    top--;
    stack[top].clean();
    return true;
}

void SearchFullUp::makeCandidate(SearchStackEntry *stack, int top, Model *start) {
    int varcount = top;
    SearchStackEntry *stackEntry;
    int *vars = new int[top];
    for (int i = 0; i < top; i++) {
        stackEntry = &stack[i];
        vars[i] = stackEntry->outerList[stackEntry->varIndex];
    }
    Relation::sort(vars, varcount);
    Relation *rel = manager->getRelation(vars, varcount, true);
    Model *newModel = new Model(start->getRelationCount() + 1);
    newModel->copyRelations(*start);
    newModel->addRelation(rel, true);
    ModelCache *cache = manager->getModelCache();
    if (!cache->addModel(newModel)) {
        //-- already exists in cache; return that one
        Model *cachedModel = cache->findModel(newModel->getPrintName());
        delete newModel;
        newModel = cachedModel;
        //-- since all models come from the cache, we can do pointer compares to see if
        //-- this model is already in the list. The model might also be the current model
        if (newModel == start)
            newModel = NULL;
        else if (((VBMManager *) manager)->applyFilter(newModel)) {
            int i;
            for (i = 0; i < parentListCount; i++) {
                if (parentList[i] == newModel)
                    break;
            }
            if (i >= parentListCount) {
                parentList[parentListCount++] = newModel;
            } else
                newModel = NULL;
        }
    } else if (((VBMManager *) manager)->applyFilter(newModel)) {
        parentList[parentListCount++] = newModel;
    }
    delete[] vars;
}

Model **SearchFullUp::search(Model *start) {
    //-- moving upwards involves finding a candidate relation for insertion, and then
    //-- verifying that all its immediate subrelations are present in the model. This
    //-- must be done for all candidate relations.
    int relationCount = start->getRelationCount();

    //-- allocate model storage. Since each relation in the model can be augmented with at
    //-- most one variable, an upper bound on the number of parents is the number of variables
    //-- times the number of relations in this model.
    int parentListMax = relationCount * (start->getRelation(0)->getVariableList()->getVarCount() - 1);
    parentList = new Model*[parentListMax];
    memset(parentList, 0, parentListMax * sizeof(Model*));
    parentListCount = 0;

    //-- The stack depth can be no more than the number of relations in the model. Allocate
    //-- the stack.
    SearchStackEntry *stack = new SearchStackEntry[relationCount];

    //-- For each model up to the next-to-last one, push the relation on the
    //-- stack and do the processing.
    for (int relIndex = 0; relIndex < start->getRelationCount() - 1; relIndex++) {
        int top = 0;
        pushRelation(stack, top, start, relIndex);
        for (;;) {
            SearchStackEntry *stacktop = &stack[top - 1];
            //-- if the innerList is empty, we can't add more relations.
            if (stacktop->innerListCount == 0) {
                while (stacktop->varIndex < stacktop->outerListCount) {
                    if (top > 1)
                        makeCandidate(stack, top, start);
                    stacktop->varIndex++;
                    stacktop->nextRelIndex = stacktop->relIndex + 1;
                }
                pop(stack, top);
                if (top == 0)
                    break;
            }
            //-- if we can't push another matching relation, then this is a candidate
            else {
                while (stacktop->varIndex < stacktop->outerListCount && !pushMatchingRelation(stack, top, start)) {
                    if (top > 1) {
                        makeCandidate(stack, top, start);
                    }
                    stacktop->varIndex++;
                    stacktop->nextRelIndex = stacktop->relIndex + 1;
                }
                if (stacktop->varIndex >= stacktop->outerListCount)
                    pop(stack, top);
                if (top == 0)
                    break;
            }
        }
    }
    delete[] stack;
    return parentList;
}

void SearchSbFullUp::recurseDirected(Model *start, int cur_var, int cur_index, int *var_indices, int *state_indices,
        int &models_found, Model **model_list) {
    VariableList *var_list = manager->getVariableList();
    bool is_directed = var_list->isDirected();
    if (cur_var >= var_list->getVarCount()) {
        if ((is_directed && (cur_index >= 2)) || (!is_directed && (cur_index >= 1))) { // make sure enough variables have been added
            Relation *new_relation = manager->getRelation(var_indices, cur_index, true, state_indices);
            for (int i = 0; i < start->getRelationCount(); i++)
                if (start->getRelation(i) == new_relation)
                    return;
            Model *model = new Model(start->getRelationCount() + 1);
            model->copyRelations(*start);
            model->addRelation(new_relation, true, manager->getModelCache()); // may not need to normalize here, or if so, may need to check if it did anything
            if (model->getRelationCount() > start->getRelationCount()) {
                addToCache(model, models_found, model_list);
            } else {
                delete model;
            }
        }
        return;
    } else {
        ocVariable *var = var_list->getVariable(cur_var);
        // first call recursion without this variable, to skip it
        recurseDirected(start, cur_var + 1, cur_index, var_indices, state_indices, models_found, model_list);
        // then call it with each of the states
        if (!is_directed || (is_directed && (cur_var != var_list->getDV()))) {
            var_indices[cur_index] = cur_var;
            for (int i = 0; i < var->cardinality; i++) {
                state_indices[cur_index] = i;
                recurseDirected(start, cur_var + 1, cur_index + 1, var_indices, state_indices, models_found,
                        model_list);
            }
        }
    }
}

bool SearchSbFullUp::addToCache(Model *model, int &models_found, Model **model_list) {
    ModelCache* cache = manager->getModelCache();
    // put the model in the cache, or use the cached one if already there
    if (!cache->addModel(model)) {
        Model *cached_model = cache->findModel(model->getPrintName());
        delete model;
        model = cached_model;
    }
    model->completeSbModel();
    if (manager->computeDF(manager->getTopRefModel()) - manager->computeDF(model) <= 1e-36) {
        model = manager->getTopRefModel();
    }
    // check if this model is in the return list, so we don't add a duplicate
    bool found = false;
    for (int j = 0; j < models_found; j++) {
        if (model_list[j] == model) {
            found = true;
            break;
        }
    }
    if (!found) {
        if (((SBMManager *) manager)->applyFilter(model))
            model_list[models_found++] = model;
        return true;
    }
    return false;
}

//----- Bottom-up search through all state-based models -----
Model** SearchSbFullUp::search(Model* start) {
    if (start == manager->getTopRefModel())
        return NULL;
    Model **models = NULL; // return list
    VariableList *var_list = manager->getVariableList();
    int var_count = var_list->getVarCount();
    int rel_count = start->getRelationCount();
    int max_models = 0;
    int models_found = 0;
    if (var_list->isDirected()) {
        if (rel_count > 1) {
            // We attempt to add all possible states, skipping those that are already included.
            // New relations can consist of one or more IVs and the DV, each with only one state.
            // In the case of a binary DV, new relations contain the full DV.
            // The model creation process should take care of states that combine to larger relations.
            int *var_indices = new int[var_count];
            int *state_indices = new int[var_count];
            memset(var_indices, 0, var_count * sizeof(int));
            memset(state_indices, 0, var_count * sizeof(int));
            // compute number of models we're going to generate
            ocVariable *DV = var_list->getVariable(var_list->getDV());
            max_models = DV->cardinality;
            if (DV->cardinality == 2)
                max_models = 1;
            // (If this list is too large, we could start smaller and use growStorage)
            for (int i = 0; i < var_count; i++) {
                if (i == var_list->getDV())
                    continue;
                max_models *= var_list->getVariable(i)->cardinality + 1;
            }
            models = new Model *[max_models + 1];
            memset(models, 0, sizeof(Model *) * (max_models + 1));
            int cur_var = 0, cur_index = 0, model_count = 0;
            var_indices[cur_index] = var_list->getDV();
            if (DV->cardinality > 2) {
                for (int i = 0; i < DV->cardinality; i++) {
                    state_indices[cur_index] = i;
                    recurseDirected(start, cur_var, cur_index + 1, var_indices, state_indices, models_found, models);
                }
            } else {
                state_indices[cur_index] = DONT_CARE;
                recurseDirected(start, cur_var, cur_index + 1, var_indices, state_indices, models_found, models);
            }
            delete[] var_indices;
            delete[] state_indices;
        } else {
            printf("SearchSbFullUp: Error. %s ", start->getPrintName());
            printf("is not an appropriate starting model for an upward, directed, state-based search.\n");
            exit(1);
        }
    } else {
        // Neutral system
        // We attempt to add all possible states, skipping those that are already included.
        // New relations can consist of one or more IVs, each with only one state.
        // The model creation process should take care of states that combine to larger relations.
        int *var_indices = new int[var_count];
        int *state_indices = new int[var_count];
        memset(var_indices, 0, var_count * sizeof(int));
        memset(state_indices, 0, var_count * sizeof(int));
        // compute number of models we're going to generate
        max_models = 1;
        // (If this list is too large, we could start smaller and use growStorage)
        for (int i = 0; i < var_count; i++)
            max_models *= var_list->getVariable(i)->cardinality + 1;
        models = new Model *[max_models + 1];
        memset(models, 0, sizeof(Model *) * (max_models + 1));
        int cur_var = 0, cur_index = 0, model_count = 0;
        recurseDirected(start, cur_var, cur_index, var_indices, state_indices, models_found, models);
        delete[] var_indices;
        delete[] state_indices;
    }
    return models;
}

//----- Top-down search through loopless models -----

/*
 * this algorithm is a a modification of that proposed by Krippendorf. His algorithm
 * replaces a relation K by (K-v'):(K-v"), where v' and v" satisfy the requirement that
 * no other relation besides K contains both. This procedure is performed for all
 * relations, and for all pairs of variables in each relation.
 *
 * This is equivalent to the simpler algorithm that, for all pairs v' and v", the pair
 * occurs in exactly one relation. For such a pair, the relation containing them both
 * is replaced as above.
 *
 * This algorithm is simpler to implement and also eliminates consideration of the same
 * pair of variables more than once.
 */
Model **SearchLooplessDown::search(Model *start) {
    VariableList *varList = manager->getVariableList();
    int varcount = varList->getVarCount();
    bool isDirected = varList->isDirected();
    int relCount = start->getRelationCount();
    if (isDirected) {
        int dvIndex = varList->getDV();
        // must have one relation with all vars; or one of IVs and one with DV plus some IVs
        if ((relCount > 2) || (relCount < 1))
            return NULL;
        Relation *rel, *ivRel;
        if (relCount == 1) {
            if (start != manager->getTopRefModel())
                return NULL;
            rel = start->getRelation(0);
            ivRel = manager->getChildRelation(rel, dvIndex);
        } else {
            rel = start->getRelation(1);
            ivRel = start->getRelation(0);
            if (rel->isIndependentOnly()) {
                rel = start->getRelation(0);
                ivRel = start->getRelation(1);
            }
        }
        if (rel->isIndependentOnly() || !ivRel->isIndependentOnly())
            return NULL;
        int activeIVs = rel->getVariableCount() - 1;
        if (activeIVs == 0)
            return NULL;
        int indices[activeIVs];
        if (rel->getIndependentVariables(indices, activeIVs) != activeIVs)
            return NULL;
        // allocate space for that many models
        Model **models = new Model *[activeIVs + 1];
        memset(models, 0, (activeIVs + 1) * sizeof(Model*));
        Relation *newRel;
        Model *model;
        int slot = 0;
        // for each IV
        for (int i = 0; i < activeIVs; i++) {
            // create a child relation minus that IV
            newRel = manager->getChildRelation(rel, indices[i]);
            // create a model with the IV-only relation, and the new relation
            model = new Model(2);
            model->addRelation(ivRel);
            model->addRelation(newRel);
            // put in cache, or use the cached one if already there
            ModelCache *cache = manager->getModelCache();
            if (!cache->addModel(model)) {
                Model *cachedModel = cache->findModel(model->getPrintName());
                delete model;
                model = cachedModel;
            }
            if (((VBMManager *) manager)->applyFilter(model))
                models[slot++] = model;
        }
        return models;
    } else {
        int maxChildren = varcount * (varcount - 1);
        int i, j;

        //-- worst case - need a list with a slot for each pair of variables
        //-- plus one for null termination of list
        Model **models = new Model *[maxChildren + 1];
        memset(models, 0, (maxChildren + 1) * sizeof(Model*));
        Model *model;
        int slot = 0;

        //-- consider each pair of variables
        for (i = 0; i < varcount - 1; i++) {
            for (j = i + 1; j < varcount; j++) {
                //-- construct a variable list for this pair, and check for containment
                int pair[2];
                int includeCount = 0;
                int includeID;
                int relNumber;
                pair[0] = i;
                pair[1] = j;
                Relation *rel;
                for (relNumber = 0; relNumber < relCount; relNumber++) {
                    rel = start->getRelation(relNumber);
                    if (ocContainsVariables(rel->getVariableCount(), rel->getVariables(), 2, pair)) {
                        if (++includeCount > 1)
                            break; //pair in more than one relation
                        includeID = relNumber;
                    }
                }
                //-- did we get a hit? If so, construct the child model
                if (includeCount == 1) {
                    model = new Model(relCount + 1);
                    model->copyRelations(*start, includeID);
                    rel = start->getRelation(includeID);
                    model->addRelation(manager->getChildRelation(rel, i));
                    model->addRelation(manager->getChildRelation(rel, j));

                    //-- put in cache, or use the cached one if already there
                    ModelCache *cache = manager->getModelCache();
                    if (!cache->addModel(model)) {
                        Model *cachedModel = cache->findModel(model->getPrintName());
                        delete model;
                        model = cachedModel;
                    }
                    if (((VBMManager *) manager)->applyFilter(model))
                        models[slot++] = model;
                }
            }
        }
        return models;
    }
}

void SearchSbLooplessUp::recurseDirected(int cur_var, int cur_index, int *var_indices, int *state_indices,
        int &models_found, Model **model_list) {
    VariableList *var_list = manager->getVariableList();
    if (cur_var >= var_list->getVarCount()) {
        if (cur_index >= 2) { // make sure enough variables have been added
            Model *model = new Model(3);
            model->addRelation(manager->getIndRelation(), false);
            model->addRelation(manager->getDepRelation(), false);
            Relation *new_relation = manager->getRelation(var_indices, cur_index, true, state_indices);
            model->addRelation(new_relation, true, manager->getModelCache());
            addToCache(model, models_found, model_list);
        }
        return;
    } else {
        ocVariable *var = var_list->getVariable(cur_var);
        // first call recursion without this variable, to skip it
        recurseDirected(cur_var + 1, cur_index, var_indices, state_indices, models_found, model_list);
        // then call it with each of the states
        if (cur_var != var_list->getDV()) {
            var_indices[cur_index] = cur_var;
            for (int i = 0; i < var->cardinality; i++) {
                state_indices[cur_index] = i;
                recurseDirected(cur_var + 1, cur_index + 1, var_indices, state_indices, models_found, model_list);
            }
        }
    }
}

bool SearchSbLooplessUp::addToCache(Model *model, int &models_found, Model **model_list) {
    ModelCache* cache = manager->getModelCache();
    Model* cached_model = NULL;
    // put the model in the cache, or use the cached one if already there
    if (!cache->addModel(model)) {
        Model *cached_model = cache->findModel(model->getPrintName());
        delete model;
        model = cached_model;
    }
    // check if this model is in the return list, so we don't add a duplicate
    bool found = false;
    for (int j = 0; j < models_found; j++) {
        if (model_list[j] == model) {
            found = true;
            break;
        }
    }
    if (!found) {
        if (((SBMManager *) manager)->applyFilter(model)) {
            model->completeSbModel();
            model_list[models_found++] = model;
            return true;
        }
    }
    return false;
}

//----- Bottom-up search through state-based loopless models -----
Model **SearchSbLooplessUp::search(Model *start) {
    if (start == manager->getTopRefModel())
        return NULL;
    Model **model_list = NULL; // return list
    VariableList *var_list = manager->getVariableList();
    int var_count = var_list->getVarCount();
    int rel_count = start->getRelationCount();
    int max_models = 0;
    int models_found = NULL;
    if (manager->hasLoops(start)) {
        printf("SearchSbLooplessUp: Error. Cannot complete a loopless search starting from a model with a loop.\n");
        exit(1);
    }
    ocVariable *DV = var_list->getVariable(var_list->getDV());
    if (var_list->isDirected()) {
        // Directed system
        // "start" must either have 2 relations (IV:DV) or 3 (IV:DV:...). In the first case, we add a third relation,
        // while in the second case, we add new states/vars to the existing third relation.
        if ((rel_count == 2) && (DV->cardinality != 2 || start == manager->getBottomRefModel())) {
            if (!start->getRelation(0)->isIndependentOnly() && !start->getRelation(1)->isIndependentOnly()) {   // Not sure if this case ever happens now
                model_list = new Model *[2];
                memset(model_list, 0, sizeof(Model *) * 2);
                addToCache(manager->getTopRefModel(), models_found, model_list);
                return model_list;
            }
            // New relations can consist of one or more IVs and the DV, each with only one state.
            // In the case of a binary DV, new relations contain the full DV.
            int *var_indices = new int[var_count];
            int *state_indices = new int[var_count];
            memset(var_indices, 0, var_count * sizeof(int));
            memset(state_indices, 0, var_count * sizeof(int));
            // compute number of models we're going to generate
            max_models = DV->cardinality;
            if (DV->cardinality == 2)
                max_models = 1;
            // (If this list is too large, we could start smaller and use growStorage)
            for (int i = 0; i < var_count; i++) {
                if (i == var_list->getDV())
                    continue;
                max_models *= var_list->getVariable(i)->cardinality + 1;
            }
            model_list = new Model *[max_models + 1];
            memset(model_list, 0, sizeof(Model *) * (max_models + 1));
            int cur_var = 0, cur_index = 0, model_count = 0;
            var_indices[cur_index] = var_list->getDV();
            if (DV->cardinality > 2) {
                for (int i = 0; i < DV->cardinality; i++) {
                    state_indices[cur_index] = i;
                    recurseDirected(cur_var, cur_index + 1, var_indices, state_indices, models_found, model_list);
                }
            } else {
                state_indices[cur_index] = DONT_CARE;
                recurseDirected(cur_var, cur_index + 1, var_indices, state_indices, models_found, model_list);
            }
            delete[] var_indices;
            delete[] state_indices;
        } else if ((rel_count == 3) || (rel_count == 2 && DV->cardinality == 2 && start != manager->getBottomRefModel())) {
            // Identify the relation to modify. It should have a DV and one or more IVs, each with either a single
            // state or the entire variable.  The relation is modified by replacing a single-state variable with a
            // complete variable, or by adding a new complete variable.
            // For DV with card=2, we use whichever relation is not ind-only
            Relation* rel = NULL;
            for (int i = 0; i < rel_count; i++) {
                if (DV->cardinality == 2) {
                    if (!start->getRelation(i)->isIndependentOnly()) {
                        rel = start->getRelation(i);
                        break;
                    }
                } else {
                    if (!start->getRelation(i)->isIndependentOnly() && !start->getRelation(i)->isDependentOnly()) {
                        rel = start->getRelation(i);
                        break;
                    }
                }
            }
            if (rel == NULL) {
                printf("SearchSbLooplessUp: Error. Model lacks the appropriate component to continue search.\n");
                exit(1);
                return NULL;
            }
            int rel_var_count = rel->getVariableCount();
            max_models = var_count;
            model_list = new Model *[max_models + 1];
            memset(model_list, 0, sizeof(Model *) * (max_models + 1));
            int *var_indices = new int[rel_var_count + 1];
            int *state_indices = new int[rel_var_count + 1];
            int old_value;
            int new_rel_count = 0;
            Model* model;
            Relation *new_relation;
            memset(var_indices, 0, (rel_var_count + 1) * sizeof(int));
            memset(state_indices, 0, (rel_var_count + 1) * sizeof(int));
            memcpy(var_indices, rel->getVariables(), rel_var_count * sizeof(int));
            memcpy(state_indices, rel->getStateIndices(), rel_var_count * sizeof(int));
            // Look for a variable with a single state, to replace with the full variable
            for (int i = 0; i < rel_var_count; i++) {
                if (var_indices[i] == var_list->getDV())
                    continue;
                if (state_indices[i] != DONT_CARE) {
                    old_value = state_indices[i];
                    state_indices[i] = DONT_CARE;
                    new_relation = manager->getRelation(var_indices, rel_var_count, true, state_indices);
                    if (new_relation == manager->getTopRefModel()->getRelation(0))
                        break;
                    new_rel_count++;
                    model = new Model(3);
                    model->addRelation(manager->getIndRelation(), false);
                    model->addRelation(manager->getDepRelation(), false);
                    model->addRelation(new_relation, false, manager->getModelCache());
                    addToCache(model, models_found, model_list);
                    state_indices[i] = old_value;
                }
            }
            // Next, look for missing variables, and add them in whole.
            memset(var_indices, 0, (rel_var_count + 1) * sizeof(int));
            memset(state_indices, 0, (rel_var_count + 1) * sizeof(int));
            memcpy(var_indices, rel->getVariables(), rel_var_count * sizeof(int));
            memcpy(state_indices, rel->getStateIndices(), rel_var_count * sizeof(int));
            int missing_vars[var_count];
            int miss_count = rel->copyMissingVariables(missing_vars, var_count);
            for (int i = 0; i < miss_count; i++) {
                var_indices[rel_var_count] = missing_vars[i];
                state_indices[rel_var_count] = DONT_CARE;
                new_relation = manager->getRelation(var_indices, rel_var_count+1, true, state_indices);
                if (new_relation == manager->getTopRefModel()->getRelation(0))
                    break;
                new_rel_count++;
                model = new Model(3);
                model->addRelation(manager->getIndRelation(), false);
                model->addRelation(manager->getDepRelation(), false);
                model->addRelation(new_relation, false, manager->getModelCache());
                addToCache(model, models_found, model_list);
            }
            // If the relation has all of the variables possible, and no new relations are found, then
            // the next step is the top model.
            if (rel_var_count == manager->getVariableList()->getVarCount() && new_rel_count == 0) {
                model = new Model(1);
                model->addRelation(manager->getTopRefModel()->getRelation(0), false);
                addToCache(model, models_found, model_list);
            }
            delete[] state_indices;
            delete[] var_indices;
        } else {
            if (rel_count == 1) {
                return NULL;
            }
            printf("SearchSbLooplessUp: Error. ");
            printf("%s is not an appropriate model for an upward, loopless search.\n", start->getPrintName());
            exit(1);
        }
    } else {
        // Neutral system
        printf("SearchSbLooplessUp: Error. ");
        printf("Neutral loopless upward search is not yet implemented for state-based systems.\n");
        exit(1);
    }
    return model_list;
}

//----- Bottom-up search through loopless models -----
/*
 * For bottom-up search of directed systems, at least for those with a single
 * dependent variable, the set of loopless models is equivalent to the set of
 * Single-Predictive-Component (SPC) models. These can be easily constructed
 * by taking each variable from the independent variable set, which is not in
 * the dependent (predictive) component of the model, and adding it. All such
 * new models will still have a single predictive component, and all possible
 * parents will be created.
 */
Model **SearchLooplessUp::search(Model *start) {
    VariableList *varList = manager->getVariableList();
    int varcount = varList->getVarCount();
    int relcount = start->getRelationCount();
    int maxChildren = varcount * (relcount - 1);
    int i, r;
    int indOnlyRel = -1;

    if (manager->hasLoops(start)) {
        printf("SearchLooplessUp: Error. Cannot complete a loopless search starting from a model with a loop.\n");
        exit(1);
        return NULL;
    }
    // Neutral loopless up
    if (!varList->isDirected()) {
        maxChildren = 4;
        Model **models = new Model *[maxChildren];
        Model *model, *cachedModel;
        memset(models, 0, maxChildren * sizeof(Model*));
        int modelsFound = 0;
        int *pair = new int[2];
        int *newRelVars = new int[varcount+1];
        int newRelVarCount = 0;
        Relation *pairRel, *newRel;
        bool found;
        for (int i = 0; i < varcount; i++) {
            for (int j = i+1; j < varcount; j++) {
                pair[0] = i;
                pair[1] = j;
                pairRel = manager->getRelation(pair, 2, false);
                if (start->containsRelation(pairRel))
                    continue;
                for (int m = 0; m < relcount; m++) {
                    if (start->getRelation(m)->findVariable(i) != -1) {
                        for (int n = 0; n < relcount; n++) {
                            if (start->getRelation(n)->findVariable(j) != -1) {
                                newRelVarCount = 2;
                                newRelVars[0] = i;
                                newRelVars[1] = j;
                                for (int k = 0; k < start->getRelation(m)->getVariableCount(); k++) {
                                    if (start->getRelation(n)->findVariable(start->getRelation(m)->getVariable(k)) != -1) {
                                        newRelVars[newRelVarCount] = start->getRelation(m)->getVariable(k);
                                        newRelVarCount++;
                                    }
                                }
                                model = new Model(relcount+1);
                                model->copyRelations(*start);
                                newRel = manager->getRelation(newRelVars, newRelVarCount, true);
                                model->addRelation(newRel, true);
                                // put the model in the cache, or use the cached one if already there
                                ModelCache *cache = manager->getModelCache();
                                if (!cache->addModel(model)) {
                                    cachedModel = cache->findModel(model->getPrintName());
                                    delete model;
                                    model = cachedModel;
                                }
                                if (manager->hasLoops(model))
                                    continue;
                                // check if this model is in the return list, so we don't add a duplicate
                                found = false;
                                for (int l = 0; l < modelsFound; l++) {
                                    if (models[l] == model) {
                                        found = true;
                                        break;
                                    }
                                }
                                if (!found) {
                                    if (((VBMManager *) manager)->applyFilter(model)) {
                                        if (modelsFound >= maxChildren - 1) {
                                            const int GROWTH_FACTOR = 2;
                                            while (modelsFound >= maxChildren - 1) {
                                                models = (Model**) growStorage(models, maxChildren*sizeof(Model*), GROWTH_FACTOR);
                                                maxChildren *= GROWTH_FACTOR;
                                            }
                                        }
                                        models[modelsFound++] = model;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        delete[] pair; delete[] newRelVars;
        return models;
    }

    //-- determine which relation is the one containing only independent variables.
    //-- this one is not modified during the search.
    for (i = 0; i < relcount; i++) {
        if (start->getRelation(i)->isIndependentOnly()) {
            indOnlyRel = i;
            break;
        }
    }
    if (indOnlyRel == -1) { // no independent-only relation; malformed model for this algorithm
        return NULL;
    }

    Model **models = new Model *[maxChildren + 1];
    Model *model;
    int slot = 0;
    memset(models, 0, (maxChildren + 1) * sizeof(Model*));

    //-- for each variable, see if we can add it to each relation (other than the indonly one)
    for (i = 0; i < varcount; i++) {
        for (r = 0; r < relcount; r++) {
            if (r == indOnlyRel)
                continue;
            Relation *rel = start->getRelation(r);
            if (-1 == rel->findVariable(i)) {
                model = new Model(relcount + 1);
                model->copyRelations(*start, r);
                int relvarcount = rel->getVariableCount();
                int *relvars = new int[relvarcount + 1];
                rel->copyVariables(relvars, relvarcount);
                relvars[relvarcount++] = i;
                Relation *newRelation = manager->getRelation(relvars, relvarcount, true);
                model->addRelation(newRelation);
                //-- put in cache, or use the cached one if already there
                ModelCache *cache = manager->getModelCache();
                if (!cache->addModel(model)) {
                    Model *cachedModel = cache->findModel(model->getPrintName());
                    delete model;
                    model = cachedModel;
                }
                if (((VBMManager *) manager)->applyFilter(model)) {
                    models[slot++] = model;
                }
                delete relvars;
            }
        }
    }
    return models;
}

//----- Bottom-up disjoint search -----

/*
 * Disjoint search considers only models where there are no overlaps among the terms
 * containing the dependent variable. For a given model, there are two methods to generate
 * parents:
 * For each pair of terms in the model, combine the pair. Note that since there was no
 * overlap among the terms, combining two terms preserves this property.
 * For each variable not present in one of the current terms, add a term which contains
 * only that variable (and the dependent variable).
 */
Model **SearchDisjointUp::search(Model *start) {
    VariableList *varList = manager->getVariableList();
    int varcount = varList->getVarCount();
    int relcount = start->getRelationCount();
    int i, r, r2, relvarcount;
    int indOnlyRel = -1;
    int depVar = -1;
    bool isDirected = manager->getVariableList()->isDirected();

    //-- the maximum number of generated models (actually parents)
    //-- is the sum of the number of unused variables, and the
    //-- number of pairs of terms. An upper bound is a sum of the
    //-- total number of IVs and the possible pairs.
    int maxChildren = (varcount) + ((relcount - 1) * (relcount - 2)) / 2;

    //-- determine which relation is the one containing only independent variables.
    //-- this one is not modified during the search.
    if (isDirected) {
        for (i = 0; i < relcount; i++) {
            if (start->getRelation(i)->isIndependentOnly()) {
                indOnlyRel = i;
                break;
            }
        }

        //-- find the dependent variable
        for (i = 0; i < varcount; i++) {
            if (varList->getVariable(i)->dv) {
                depVar = i;
                break;
            }
        }
        if (depVar == -1) { // no dep variable; malformed model for this algorithm
            return NULL;
        }
    }

    Model **models = new Model *[maxChildren + 1];
    Model *model;
    int slot = 0;
    memset(models, 0, (maxChildren + 1) * sizeof(Model*));

    //-- for each variable, see if we can add it (only if it doesn't appear).
    //-- this step only applies for directed systems; for neutral systems all
    //-- variables are already present.
    if (isDirected) {
        for (i = 0; i < varcount; i++) {
            if (i == depVar)
                continue; // skip dependent variable
            bool varfound = false;
            for (r = 0; r < relcount; r++) {
                if (r == indOnlyRel)
                    continue;
                Relation *rel = start->getRelation(r);
                if (-1 != rel->findVariable(i)) {
                    varfound = true;
                    break;
                }
            }
            if (!varfound) {
                model = new Model(relcount + 1);
                model->copyRelations(*start);
                int *relvars = new int[2];
                relvars[0] = i;
                relvars[1] = depVar;
                Relation *newRelation = manager->getRelation(relvars, 2, true);
                model->addRelation(newRelation);
                //-- put in cache, or use the cached one if already there
                ModelCache *cache = manager->getModelCache();
                if (!cache->addModel(model)) {
                    Model *cachedModel = cache->findModel(model->getPrintName());
                    delete model;
                    model = cachedModel;
                }
                if (((VBMManager *) manager)->applyFilter(model))
                    models[slot++] = model;
            }
        }
    }

    //-- now try combining pairs of models
    Relation *rel, *rel2;
    for (r = 0; r < relcount; r++) {
        if (r == indOnlyRel)
            continue;
        for (r2 = r + 1; r2 < relcount; r2++) {
            if (r2 == indOnlyRel)
                continue;
            model = new Model(relcount + 1);
            model->copyRelations(*start, r, r2);
            rel = start->getRelation(r);
            rel2 = start->getRelation(r2);
            relvarcount = rel->getVariableCount() + rel2->getVariableCount();

            //-- for directed system, dep variable is counted twice; so correct for this
            if (isDirected)
                relvarcount--;

            int *relvars = new int[relvarcount];
            int copycount = rel->copyVariables(relvars, relvarcount);
            copycount += rel2->copyVariables(relvars + copycount, relvarcount - copycount, depVar);
            Relation *newRelation = manager->getRelation(relvars, copycount, true);
            model->addRelation(newRelation);
            //-- put in cache, or use the cached one if already there
            ModelCache *cache = manager->getModelCache();
            if (!cache->addModel(model)) {
                Model *cachedModel = cache->findModel(model->getPrintName());
                delete model;
                model = cachedModel;
            }
            if (((VBMManager *) manager)->applyFilter(model))
                models[slot++] = model;
        }

    }
    return models;

}

//----- Chain search -----

/*
 * Chain search is the same either top down or bottom up, because all
 * the resulting models are peers at the same level. A chain model for
 * a neutral system consists of only two-variable relations, such that
 * all but two of the variables appear in exactly two relations. Thus
 * the relations form a chain of variables, linked pairwise.
 *
 * For a directed system, the chain is similar; all relations except
 * the IV relation have three variables: the dependent variable and
 * two others.
 *
 * In both cases, the set of all chain models is isomorphic to the
 * set of all orderings of the variables. This algorithm generates
 * the models by first generating all orderings, and generating a
 * model for each.
 *
 * Actually, every model appears twice because forward and backward
 * orderings generate the same model
 */

//-- can you believe there's no factorial function in the math library?
long factorial(long n) {
    return (n <= 1) ? 1 : factorial(n - 1) * n;
}

long comb(long n, long m) {
    return factorial(n) / (factorial(n - m) * factorial(m));
}

// recursive function to generate chain models
bool SearchChain::makeChainModels() {
    int relVars[3];
    int relCount, relVarCount;
    int indVarCount = isDirected ? varCount - 1 : varCount;

    //-- if the model list is full, its an internal error
    if (slot >= maxChildren)
        return false;

    //-- if we've ordered all the variables, generate a model
    //-- each pair of adjacent variables generates a relation
    //-- for directed systems, the dv is added
    if (stackPtr >= indVarCount) {
        relCount = varCount - 1;
        relVarCount = 2;
        if (isDirected) {
            relCount++;
            relVarCount++;
        }
        Model *model = new Model(relCount);
        if (isDirected)
            model->addRelation(indOnlyRel, false);
        for (int i = 0; i < indVarCount - 1; i++) {
            relVars[0] = varStack[i];
            relVars[1] = varStack[i + 1];
            if (isDirected)
                relVars[2] = depVar;
            Relation *newRelation = manager->getRelation(relVars, relVarCount, true);
            model->addRelation(newRelation);
        }

        //-- put in cache, or use the cached one if already there
        ModelCache *cache = manager->getModelCache();
        static char *oldBrk = 0;
        if (oldBrk == 0)
            oldBrk = (char*) sbrk(0);
        double used = ((char*) sbrk(0)) - oldBrk;
        if (!cache->addModel(model)) {
            Model *cachedModel = cache->findModel(model->getPrintName());
            delete model;
            model = cachedModel;
        }
        if (((VBMManager *) manager)->applyFilter(model))
            models[slot++] = model;
    } else {
        // generate all possible successors, but skip any variables already in the list
        for (int idx = 0; idx < varCount; idx++) {
            int vidx;
            if (idx == depVar)
                continue; // skip the dependent variable
            for (vidx = 0; vidx < stackPtr; vidx++) {
                if (varStack[vidx] == idx)
                    break;
            }
            if (vidx >= stackPtr) {
                varStack[stackPtr++] = idx;
                if (!makeChainModels())
                    return false;
                stackPtr--;
            }
        }
    }
    return true;
}

Model **SearchChain::search(Model *start) {
    VariableList *varList = manager->getVariableList();
    varCount = varList->getVarCount();
    int i;
    indOnlyRel = NULL;
    depVar = -1;
    isDirected = manager->getVariableList()->isDirected();

    //-- the number of generated models is the number of distinct
    //-- sequences of variables, or n!
    maxChildren = factorial(varCount);
    models = new Model *[maxChildren + 1];
    memset(models, 0, (maxChildren + 1) * sizeof(Model*));

    //-- determine which relation is the one containing only independent variables.
    //-- this one is not modified during the search.

    if (isDirected) {
        for (int r = 0; r < start->getRelationCount(); r++) {
            if (start->getRelation(r)->isIndependentOnly()) {
                indOnlyRel = start->getRelation(r);
            }
        }

        //-- find the dependent variable
        for (i = 0; i < varCount; i++) {
            if (varList->getVariable(i)->dv) {
                depVar = i;
                break;
            }
        }
        if (depVar == -1) { // no dep variable; malformed model for this algorithm
            return NULL;
        }
    }
    //-- initialize variables used by recursive makeChainModels
    slot = 0;
    varStack = new int[varCount];
    stackPtr = 0;
    //-- recursively process the variable list, generating
    //-- all possible sequences.
    makeChainModels();
    delete varStack;
    return models;
}

// Alireza
Model **SearchDisjointDown::search(Model *start) {

    VariableList *varList = manager->getVariableList();
    int varcount = varList->getVarCount();
    bool isDirected = varList->isDirected();
    int relCount = start->getRelationCount();
    int numModels = 100;
    Model **models = new Model *[numModels + 1];
    memset(models, 0, (numModels + 1) * sizeof(Model*));

    // cout << endl <<  " directed:" << isDirected << " rel count:" << relCount <<  endl;
    if (isDirected) {
        /*
         int dvIndex = varList->getDV();
         // must have one relation with all vars; or one of IVs and one with DV plus some IVs
         if ((relCount > 2) || (relCount < 1))
         return NULL;
         Relation *rel, *ivRel;
         if (relCount == 1) {
         if (start != manager->getTopRefModel())
         return NULL;
         rel = start->getRelation(0);
         ivRel = manager->getChildRelation(rel, dvIndex);
         } else {
         rel = start->getRelation(1);
         ivRel = start->getRelation(0);
         if (rel->isIndependentOnly()) {
         rel = start->getRelation(0);
         ivRel = start->getRelation(1);
         }
         }
         if (rel->isIndependentOnly() || !ivRel->isIndependentOnly()) return NULL;
         int activeIVs = rel->getVariableCount() - 1;
         if (activeIVs == 0) return NULL;
         int indices[activeIVs];
         if (rel->getIndependentVariables(indices, activeIVs) != activeIVs)
         return NULL;
         // allocate space for that many models
         Model **models = new Model *[activeIVs + 1];
         memset(models, 0, (activeIVs + 1) * sizeof(Model*));
         Relation *newRel;
         Model *model;
         int slot = 0;
         // for each IV
         for (int i=0; i < activeIVs; i++) {
         // create a child relation minus that IV
         newRel = manager->getChildRelation(rel, indices[i]);
         // create a model with the IV-only relation, and the new relation
         model = new Model(2);
         model->addRelation(ivRel);
         model->addRelation(newRel);
         // put in cache, or use the cached one if already there
         ModelCache *cache = manager->getModelCache();
         if (!cache->addModel(model)) {
         Model *cachedModel = cache->findModel(model->getPrintName());
         delete model;
         model = cachedModel;
         }
         if (manager->applyFilter(model)) models[slot++] = model;
         }
         */
        return NULL;
    } else { // not directed search starts here
        //cout << " hi undirected" <<endl;
        // index for the generated models
        int mi = 0;
        // iterate over relations
        for (int ri = 0; ri < relCount; ri++) {

            Relation* rel = start->getRelation(ri);
            int relvarcnt = rel->getVariableCount();
            //cout << "1:" << endl;
            if (relvarcnt >= 2) {
                int varList[relvarcnt];
                rel->copyVariables(varList, relvarcnt, -1);
                for (int vi = 0; vi < relvarcnt; vi++) {

                    Model* m = new Model(relCount + 1);
                    //first copy all the relations except for the ri
                    for (int rii = 0; rii < relCount; rii++) {
                        if (rii != ri) {
                            m->addRelation(start->getRelation(rii));
                        }
                    }

                    //cout << "vi: " << vi << endl;
                    Relation* crel = manager->getChildRelation(rel, varList[vi]);
                    Relation* newRelation = manager->getRelation(&varList[vi], 1, true);
                    m->addRelation(crel);
                    m->addRelation(newRelation);

                    // add the model if it is not in the cache
                    ModelCache *cache = manager->getModelCache();
                    if (!cache->addModel(m)) {
                        Model *cachedModel = cache->findModel(m->getPrintName());
                        delete m;
                        m = cachedModel;
                    }
                    if (((VBMManager *) manager)->applyFilter(m))
                        models[mi++] = m;

                    //cout << "now in here:" << endl;
                    // here we are adding the variable we droped from one of the
                    // 	relations to the other relations.
                    for (int rii = 0; rii < relCount; rii++) {
                        if (rii != ri) {
                            //cout << "vi: " << vi << " ri:"<<ri << " rii:"<< rii<<endl;
                            Model* m1 = new Model(relCount);
                            Relation* crel1 = manager->getChildRelation(rel, varList[vi]);
                            Relation* nrel1 = start->getRelation(rii);
                            int vnum = nrel1->getVariableCount() + 1;
                            int vlist2[vnum];
                            nrel1->copyVariables(vlist2, vnum, -1);
                            // add the current variable to this relation
                            vlist2[vnum - 1] = varList[vi];
                            //cout << " vlist2: " ;
                            //for ( int jj=0; jj < vnum ; jj++ ) {
                            //	cout << vlist2[jj] << " " ;
                            //}
                            //cout << endl;
                            //cout << "nh:1"<< endl;
                            // make new relation add to the model
                            Relation* newRelation1 = manager->getRelation(vlist2, vnum, true);
                            //cout << "nh:1.1"<< endl;
                            m1->addRelation(crel1);
                            m1->addRelation(newRelation1);

                            for (int riii = 0; riii < relCount; riii++) {
                                if (ri != riii && riii != rii) {
                                    m1->addRelation(start->getRelation(riii));
                                }

                            }
                            //cout << "nh:2"<< endl;
                            // add the model if it is not in the cache
                            ModelCache *cache = manager->getModelCache();
                            if (!cache->addModel(m1)) {

                                Model *cachedModel = cache->findModel(m1->getPrintName());
                                delete m1;
                                m1 = cachedModel;
                            }
                            if (((VBMManager *) manager)->applyFilter(m1))
                                models[mi++] = m1;
                            //cout << "nh:3"<< endl;
                            //cout << start->getPrintName() << " -> " << m1->getPrintName() << endl;
                        } // if rii

                    } // for rii

                    //cout << start->getPrintName() << " -> " << m->getPrintName() << endl;
                    //cout << "2:" << mi << endl;

                } //for vi
            } //if

            //cout << "3:" << endl;
        }
        //cout << "4:" << endl;
        return models;
    }
}
;
