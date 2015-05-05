/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

#include "Core.h"
#include "RelCache.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <memory.h>
#include <string.h>

static int hashcode(const char *name, int hashsize) {
    unsigned int key = 0;
    for (const char *cp = name; *cp; cp++)
        key = (key << 1) + *cp;
    return key % hashsize;
}

RelCache::RelCache() {
    hash = new Relation*[RELCACHE_HASHSIZE];
    memset(hash, 0, RELCACHE_HASHSIZE * sizeof(Relation*));
}

//-- destroy relation cache.  This also deletes all the relations held in the cache.
RelCache::~RelCache() {
    Relation *r1, *r2;
    int i;
    for (i = 0; i < RELCACHE_HASHSIZE; i++) {
        r1 = hash[i];
        while (r1) {
            r2 = r1->getHashNext();
            delete r1;
            r1 = r2;
        }
    }
    delete hash;
}

long RelCache::size() {
    long size = RELCACHE_HASHSIZE * sizeof(Relation*);
    Relation *r1;
    int i;
    for (i = 0; i < RELCACHE_HASHSIZE; i++) {
        r1 = hash[i];
        while (r1) {
            size += r1->size();
            r1 = r1->getHashNext();
        }
    }
    return size;
}

//-- delete tables from all relations
void RelCache::deleteTables() {
    Relation *r1;
    int i;
    for (i = 0; i < RELCACHE_HASHSIZE; i++) {
        r1 = hash[i];
        while (r1) {
            r1->deleteTable();
            r1 = r1->getHashNext();
        }
    }
}

//-- addRelation - put a new relation in the cache. If a matching relation already
//-- exists, an error is returned.
// [JSF] This doesn't seem to check for matches, or return errors.
bool RelCache::addRelation(class Relation *rel) {
    if (findRelation(rel->getPrintName()) != NULL)
        return false; //error; exists
    KeySegment *mask = rel->getMask();
    int hashindex = hashcode(rel->getPrintName(), RELCACHE_HASHSIZE);
    rel->setHashNext(hash[hashindex]);
    hash[hashindex] = rel;
    return true;
}

//-- findRelation - find a relation in the cache.  Null is returned if the given
//-- relation doesn't exist.
class Relation *RelCache::findRelation(const char *name) {
    int hashindex = hashcode(name, RELCACHE_HASHSIZE);
    Relation *rp = hash[hashindex];
    while (rp && strcmp(name, rp->getPrintName()) != 0)
        rp = rp->getHashNext();
    return rp; // either NULL, or the matching one
}

//-- dump - print out all relations in the cache
void RelCache::dump() {
    printf("\nDumping RelCache:\n");
    for (int i = 0; i < RELCACHE_HASHSIZE; i++) {
        if (hash[i]) {
            printf("hash chain [%d]:\n", i);
            for (Relation *rel = hash[i]; rel; rel = rel->getHashNext()) {
                rel->dump();
            }
        }
    }
}

