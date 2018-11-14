/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

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
