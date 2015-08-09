#ifndef ___VarIntersect
#define ___VarIntersect

#include "Relation.h"

struct VarIntersect {
        int startIndex; // the highest numbered relation index this intersection term represents
        Relation *rel;
        bool sign;
        int count;
        VarIntersect() :
                startIndex(0), sign(true), rel(NULL), count(1) {
        }
};

#endif
