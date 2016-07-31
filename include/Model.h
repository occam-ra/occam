#ifndef ___Model
#define ___Model

#include "ModelCache.h"
#include "Relation.h"

/**
 * Model - defines a model as a list of Relations.
 */
class Model {
    public:
        // initialize model, with space for the given number of relations
        Model(int size = 2);
        ~Model();
        void deleteStructMatrix();
        long size();

        bool isStateBased();

        // get/set relations
        void addRelation(Relation *relation, bool normalize = true, ModelCache *cache=NULL);
        int getRelations(Relation **rels, int maxRelations);
        Relation *getRelation(int index);
        int getRelationCount();
        Table *getFitTable();
        void setFitTable(Table *tbl);
        void deleteFitTable();
        void deleteRelationLinks();

        // copy relation references (but not the objects)
        void copyRelations(Model &model, int skip1 = -1, int skip2 = -1);

        // get the attribute list for the model
        class AttributeList *getAttributeList() {
            return attributeList;
        }
        void setAttribute(const char *name, double value);
        double getAttribute(const char *name);

        // get a printable name for the relation, using the variable abbreviations
        const char *getPrintName(int useInverse = 0);

        // set, get hash chain linkages
        Model *getHashNext() {
            return hashNext;
        }
        void setHashNext(Model *next) {
            hashNext = next;
        }

        // Checks if this model contains the specified relation.  That is, checks if any of
        // the model's relations *contain* this relation, not if any of them *are* this relation.
        bool containsRelation(Relation *relation, ModelCache *cache=NULL);

        // Checks to see if this model is parent (or higher) of the specified child model.
        // That is, if the "child" is between this model and the bottom on the lattice.
        bool containsModel(Model *childModel);

        bool isEquivalentTo(Model *other);
        // set and get for progenitor model.  (The model from which this one was derived in a search.)
        Model *getProgenitor() {
            return progenitor;
        }
        void setProgenitor(Model *model) {
            progenitor = model;
        }

        int getID() {
            return ID;
        }
        void setID(int number) {
            ID = number;
        }

        // print out model info
        void dump(bool detail = false);

        // state based models need to make structure matrix for DF calculation
        void makeStructMatrix(int statespace, VariableList *vars, int **stateSpaceArr);
        int* getIndicesFromKey(KeySegment *key, VariableList *vars, int statespace,
                int **stateSpaceArr, int *counter);
        void completeSbModel();
        int** makeStateSpaceArray(VariableList *varList, int statespace = 0);

        int getStateSpaceSize() { return stateSpaceSize; }
        void printStructMatrix();
        int **getStructMatrix(int *statespace, int *totalConst);
//            *statespace = stateSpaceSize;
//            *totalConst = totalConstraints;
//            return structMatrix;
//        }

 
    private:
        Relation **relations;
        Model *progenitor; // the model from which this one was derived in a search
        int ID; // ID of the model in a search list
        int relationCount;
        int maxRelationCount;
        class Table *fitTable;
        class AttributeList *attributeList;
        Model *hashNext;
        char *printName;
        char *inverseName;
        int **structMatrix;
        long totalConstraints;
        int stateSpaceSize;
};

#endif
