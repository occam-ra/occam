/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

#include <math.h>
#include <float.h>
#include "ocCore.h"
#include "_ocCore.h"
#include "ocMath.h"
#include "ocModelCache.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * ocModel.cpp - implements the ocModel class.  This represents a model, which is a
 * set of relations (and optionally the set of tables implementing those relations).
 * The model can also store a computed table, which is the fitted table to the source
 * data (e.g., computed via IPF).
 */

// initialize the model, and allocate storage for the relation pointers.
ocModel::ocModel(int size) {
    maxRelationCount = size;
    relationCount = 0;
    relations = new ocRelation*[size];
    fitTable = NULL;
    attributeList = new ocAttributeList(6);
    printName = NULL;
    inverseName = NULL;
    hashNext = NULL;
    progenitor = NULL;
    ID = 0;
    structMatrix = NULL;
}

ocModel::~ocModel() {
    if (structMatrix) {
        for (int i = 0; i < totalConstraints; i++) {
            delete[] structMatrix[i];
        }
        delete[] structMatrix;
    }
    if (printName) {
        delete printName;
        printName = NULL;
    }
    if (inverseName) {
        delete inverseName;
        inverseName = NULL;
    }
    if (relations)
        delete[] relations;     // only pointers; actual relations deleted by the relCache
    if (fitTable)
        delete fitTable;
    if (attributeList)
        delete attributeList;
}

long ocModel::size() {
    long size = sizeof(ocModel) + maxRelationCount * sizeof(ocRelation*);
    if (fitTable)
        size += fitTable->size();
    if (attributeList)
        size += attributeList->size();
    return size;
}

bool ocModel::isStateBased() {
    for (int i = 0; i < relationCount; i++) {
        if (relations[i]->isStateBased())
            return true;
    }
    return false;
}

void ocModel::deleteRelationLinks() {
    //delete [] relations;
    //relations = new ocRelation*[1];
}

void ocModel::copyRelations(ocModel &model, int skip1, int skip2) {
    int count = model.getRelationCount();
    for (int i = 0; i < count; i++) {
        ocRelation *rel = model.getRelation(i);
        if (skip1 != i && skip2 != i)
            addRelation(rel, false);
    }
}

void ocModel::setAttribute(const char *name, double value) {
    attributeList->setAttribute(name, value);
}

double ocModel::getAttribute(const char *name) {
    return attributeList->getAttribute(name);
}

//state space array
int * ocModel::getIndicesFromKey(ocKeySegment *key, ocVariableList *vars, int statespace, int **stateSpaceArr,
        int *counter) {
    int varcount = vars->getVarCount();
    int *value_l = new int[varcount];
    //maximum number of states that can constrained by a relation
    int *indices = new int[statespace];
    for (int i = 0; i < varcount; i++) {
        ocVariable *var = vars->getVariable(i);
        ocKeySegment mask = var->mask;
        int segment = var->segment;
        int value = 0;
        ocKeySegment mask1;
        if ((mask1 = (mask & key[segment])) == mask)
            value_l[i] = DONT_CARE;
        else {
            value = (key[segment] & mask) >> var->shift;
            value_l[i] = value;
        }
    }
    *counter = 0;
    int not_a_match = -1;
    for (int i = 0; i < statespace; i++) {
        for (int j = 0; j < varcount; j++) {
            if (value_l[j] == DONT_CARE)
                continue;
            if (value_l[j] != stateSpaceArr[i][j]) {
                not_a_match = 1;
                break;
            } else {
                not_a_match = 0;
            }
        }
        if (not_a_match == 0) {
            indices[(*counter)] = i;
            (*counter)++;

        }
        not_a_match = -1;

    }
    delete[] value_l;
    return indices;
}

// State-Based Structure matrix generation
void ocModel::makeStructMatrix(int statespace, ocVariableList *vars, int **stateSpaceArr) {
    if (structMatrix != NULL) return;
    int relCount = getRelationCount();
    int constraintCount = 0;
    int i = 0;
    for (i = 0; i < relCount; i++) {
        ocRelation *rel = getRelation(i);
        ocStateConstraint *sc = rel->getStateConstraints();
        if (sc != NULL)
            constraintCount += sc->getConstraintCount();
    }
    totalConstraints = constraintCount + 1;
    stateSpaceSize = statespace;
    structMatrix = new int *[constraintCount + 1];
    for (i = 0; i <= constraintCount; i++) {
        structMatrix[i] = new int[statespace];
    }
    for (i = 0; i < statespace; i++) {
        for (int j = 0; j < constraintCount; j++) {
            structMatrix[j][i] = 0;
        }
        structMatrix[constraintCount][i] = 1; //the default constraint
    }
    constraintCount = 0;
    int totalConstraintCount = 0;
    for (i = 0; i < relCount; i++) {
        ocRelation *rel = getRelation(i);
        if (rel == NULL) {
            printf("error happened in file : ocModel.cpp after getRelation\n");
            exit(1);
        }
        ocStateConstraint *sc = rel->getStateConstraints();
        if (sc == NULL) {
            printf("error happened in file : ocModel.cpp after getStateConstraints\n");
            exit(1);
        }
        constraintCount = sc->getConstraintCount();
        if (constraintCount <= 0) {
            printf("error happened in file : ocModel.cpp after getConstraintCount\n");
            exit(1);
        }
        for (int j = 0; j < constraintCount; j++) {
            ocKeySegment* key = sc->getConstraint(j);
            if (key == NULL) {
                printf("error happened in file : ocModel.cpp after getConstraint\n");
                exit(1);
            }
            int counter;
            int *indices = getIndicesFromKey(key, vars, statespace, stateSpaceArr, &counter);
            for (int k = 0; k < counter; k++) {
                structMatrix[totalConstraintCount + j][indices[k]] = 1;
            }
            delete[] indices;
        }
        totalConstraintCount += constraintCount;
    }
}

void ocModel::completeSbModel() {
    if (getRelationCount() == 0) {
        fprintf(stderr, "Error. completeSbModel(): Model contains no relations.\n");
        exit(1);
    }
    if (structMatrix != NULL) return;
    ocVariableList *varList = getRelation(0)->getVariableList();
    int stateSpace = (int) ocDegreesOfFreedom(varList) + 1; // ought to be using something longer than int
    int **stateSpaceArr = ocModel::makeStateSpaceArr(varList, stateSpace);
    this->makeStructMatrix(stateSpace, varList, stateSpaceArr);
    for (int i=0; i < stateSpace; i++) {
        delete[] stateSpaceArr[i];
    }
    delete[] stateSpaceArr;
}

int** ocModel::makeStateSpaceArr(ocVariableList *varList, int statespace) {
    int **stateSpaceArr = new int *[statespace];
    int varCount = varList->getVarCount();
    for (int i = 0; i < statespace; i++) {
        stateSpaceArr[i] = new int[varCount];
    }

    for (int i = 0; i < statespace; i++) {
        for (int j = 0; j < varCount; j++) {
            stateSpaceArr[i][j] = 0;
        }
    }
    for (int k = 0; k < varCount; k++) {
        stateSpaceArr[0][k] = 0;
    }
    int l = varCount - 1;
    int i = 0;
    int loop1 = 0;
    while (i < statespace - 1) {
        // first copy from previous state
        for (int j = 0; j < varCount; j++) {
            stateSpaceArr[i + 1][j] = stateSpaceArr[i][j];
        }
        rap: if (i + 1 == statespace)
            break;
        ocVariable *var = varList->getVariable(l);
        int card = var->cardinality;
        if (stateSpaceArr[i][l] == (card - 1)) {
            stateSpaceArr[i + 1][l] = 0;
            l--;
            if (l < 0)
                break;
            goto rap;
        } else {
            stateSpaceArr[i + 1][l]++;
            l = varCount - 1;
        }
        i++;
    }
    return stateSpaceArr;
}

// get/set relations
void ocModel::addRelation(ocRelation *newRelation, bool normalize, ocModelCache *cache) {
    if (newRelation == NULL)
        return;
    const int FACTOR = 2;
    int i, j;
    //-- if normalize, compare new relation to existing relations
    if (normalize && getRelationCount() > 0) {
        if (this->isStateBased() || newRelation->isStateBased()) {
            if (this->containsRelation(newRelation, cache))
                return;
        } else {
            for (i = 0; i < relationCount; i++) {
                if (relations[i]->contains(newRelation)) {
                    // don't need this one. Assuming caching we don't explicitly delete it since it
                    // may be referenced elsewhere.
                    return;
                } else if (newRelation->contains(relations[i])) {
                    // remove this relation from model
                    for (j = i; j < relationCount - 1; j++) {
                        relations[j] = relations[j + 1];
                    }
                    relationCount--;
                    i--; // fix loop counter since we deleted one
                }
            }
        }
    }
    //-- grow storage if needed
    while (relationCount >= maxRelationCount) {
        relations = (ocRelation**) growStorage(relations, maxRelationCount*sizeof(ocRelation*), FACTOR);
        maxRelationCount *= FACTOR;
    }
    //-- now find the spot for this newRelation and add it in
    for (i = 0; i < relationCount; i++) {
        if (newRelation->compare(relations[i]) < 0)
            break;
    }
    for (j = relationCount; j > i; j--) {
        relations[j] = relations[j - 1];
    }
    relations[i] = newRelation;
    relationCount++;
    if (printName) {
        delete printName;
        printName = NULL;
    }
    if (inverseName) {
        delete inverseName;
        inverseName = NULL;
    }
    if (structMatrix) {
        for (int i = 0; i < totalConstraints; i++) {
            delete[] structMatrix[i];
        }
        delete[] structMatrix;
        structMatrix = NULL;
    }
    if (fitTable) {
        delete fitTable;
        fitTable = NULL;
    }
    if (attributeList) {
        delete attributeList;
        attributeList = new ocAttributeList(6);
    }
}

int ocModel::getRelations(ocRelation **rels, int maxRelations) {
    int count = (relationCount < maxRelations) ? relationCount : maxRelations;
    memcpy(rels, relations, count * sizeof(ocRelation*));
    return count;
}

ocRelation *ocModel::getRelation(int index) {
    return (index < relationCount) ? relations[index] : NULL;
}

// Returns true if this model contains the specified relation; false otherwise.
bool ocModel::containsRelation(ocRelation *relation, ocModelCache *cache) {
    if (this->isStateBased() || relation->isStateBased()) {
        for (int i = 0; i < relationCount; i++) {
            if (relations[i] == relation)
                return true;
        }
        ocModel *new_model = new ocModel(this->getRelationCount() + 1);
        new_model->copyRelations(*this);
        new_model->addRelation(relation,false);
        ocModel *temp_old = NULL;
        ocModel *temp_new = NULL;
        double new_df;
        if (cache) {
            temp_new = cache->findModel(new_model->getPrintName());
        }
        if (temp_new) {
            new_df = temp_new->getAttribute(ATTRIBUTE_DF);
            if (new_df < 0.0) {
                temp_new->completeSbModel();
                new_df = ::ocDegreesOfFreedomStateBased(temp_new);
                temp_new->setAttribute(ATTRIBUTE_DF, new_df);
            }
        } else {
            new_model->completeSbModel();
            new_df = ::ocDegreesOfFreedomStateBased(new_model);
        }
        double df = this->getAttribute(ATTRIBUTE_DF);
        if (df < 0.0) { //-- not set yet
            if (cache) {
                temp_old = cache->findModel(this->getPrintName());
            }
            if (temp_old) {
                df = temp_old->getAttribute(ATTRIBUTE_DF);
                if (df < 0.0) {
                    temp_old->completeSbModel();
                    df = ::ocDegreesOfFreedomStateBased(temp_old);
                    temp_old->setAttribute(ATTRIBUTE_DF, df);
                }
            } else {
                this->completeSbModel();
                df = ::ocDegreesOfFreedomStateBased(this);
                this->setAttribute(ATTRIBUTE_DF, df);
            }
        }
        delete new_model;
        if (fabs(df - new_df) < DBL_EPSILON) {
            return true;
        }
        return false;
    } else {
        for (int i = 0; i < relationCount; i++) {
            if (relations[i]->contains(relation))
                return true;
        }
        return false;
    }
}

bool ocModel::containsModel(ocModel *other) {
    for (int i = 0; i < other->getRelationCount(); i++) {
        if (!this->containsRelation(other->getRelation(i))) {
            return false;
        }
    }
    return true;
}

bool ocModel::isEquivalentTo(ocModel *other) {
    if (this->isStateBased() || other->isStateBased()) {
        // might be good to check if DFs are equal first, as a faster check
        if ((this == other) || strcmp(this->getPrintName(),other->getPrintName()) == 0) {
            return true;
        }
        if (this->containsModel(other) && other->containsModel(this)) {
            return true;
        }
        return false;
    } else {
        if (this == other) {
            return true;
        }
    }
    return false;
}

int ocModel::getRelationCount() {
    return relationCount;
}

ocTable *ocModel::getFitTable() {
    return fitTable;
}

void ocModel::setFitTable(ocTable *tbl) {
    fitTable = tbl;
}

void ocModel::deleteFitTable() {
    if (fitTable) {
        delete fitTable;
        fitTable = NULL;
    }
}

const char * ocModel::getPrintName(int useInverse) {
    int i, len = 0;
    const char *name;
    bool isDirected = relations[0]->getVariableList()->isDirected();
    int indOnlyRel = -1;
    int useIVI = 0;
    int notUsingIVI = 0;
    if ((printName == NULL && useInverse != 1) || (inverseName == NULL && useInverse == 1)) {
        for (i = 0; i < relationCount; i++) {
            const char *name;
            //-- for directed systems, figure out which relation is the indOnly one
            if (isDirected && relations[i]->isIndependentOnly()) {
                indOnlyRel = i;
                name = "IV";
            } else if (!isDirected && (relations[i]->getVariableCount() == 1) && !relations[i]->isStateBased()) {
                useIVI++;
                name = relations[i]->getPrintName(useInverse);
                notUsingIVI = strlen(name) + 1;
                continue;
            } else {
                name = relations[i]->getPrintName(useInverse);
            }
            len += strlen(name) + 1;
        }
        if (useIVI > 1)
            len += 3 + 1;
        else if (useIVI == 1)
            len += notUsingIVI;
        char *tempName = new char[len + 1];
        char *cp = tempName;
        *cp = '\0';

        //-- format the name. For directed systems put the string 'IV:' first,
        //-- and skip the independent-only relation
        if (indOnlyRel >= 0) {
            strcpy(cp, "IV");
            cp += strlen(cp);
        } else if (useIVI > 1) {
            strcpy(cp, "IVI");
            cp += strlen(cp);
        }
        for (i = 0; i < relationCount; i++) {
            if (i == indOnlyRel)
                continue;
            if ((useIVI > 1) && (relations[i]->getVariableCount() == 1) && !relations[i]->isStateBased())
                continue;
            // if the string isn't empty, put in a colon separator
            if (cp != tempName)
                *(cp++) = ':';
            name = relations[i]->getPrintName(useInverse);
            strcpy(cp, name);
            cp += strlen(name);
        }
        *cp = '\0';
        if (useInverse == 0)
            printName = tempName;
        else
            inverseName = tempName;
    }
    if (useInverse == 0)
        return printName;
    else
        return inverseName;
}

void ocModel::printStructMatrix() {
    int statespace;
    int Total_const;
    int **str_matrix = getStructMatrix(&statespace, &Total_const);
    if (str_matrix != NULL) {
        for (int i = 0; i < Total_const; i++) {
            for (int j = 0; j < statespace; j++) {
                printf("%d,", str_matrix[i][j]);
            }
            printf("\n");
        }
    }
}

void ocModel::dump(bool detail) {
    //printf("\tocModel: %s\n", getPrintName());
    attributeList->dump();
    printf("\n");
    printf("\t\tSize: %d,\tRelCount: %d,\tMaxRel:%d\n", size(), getRelationCount(), maxRelationCount);
    if (detail) {
        if (fitTable)
            printf(",\tFitTable: %d", fitTable->size());
        for (int i = 0; i < relationCount; i++) {
            relations[i]->dump();
        }
    }
    printf("\n");

}

