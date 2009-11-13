/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

#include "ocCore.h"
#include "ocRelCache.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <memory.h>

static int hashcode(ocKeySegment *key, int keysize, int hashsize)
{
    //-- compute a hashcode, an integer from 0..hashsize-1, for the key.
    //-- this is done by XOR of the key segments, and then modulus
    ocKeySegment k = 0;
    for (int i = 0; i < keysize; i++) k ^= key[i];
    return k % hashsize;
}


ocRelCache::ocRelCache()
{
    hash = new ocRelation*[RELCACHE_HASHSIZE];
    memset(hash, 0, RELCACHE_HASHSIZE*sizeof(ocRelation*));
}


//-- destroy relation cache.  This also deletes all the relations held in the cache.
ocRelCache::~ocRelCache()
{
    ocRelation *r1, *r2;
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


long ocRelCache::size()
{
    long size = RELCACHE_HASHSIZE * sizeof(ocRelation*);
    ocRelation *r1;
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
void ocRelCache::deleteTables()
{
    ocRelation *r1;
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
bool ocRelCache::addRelation(class ocRelation *rel)
{
    ocKeySegment *mask = rel->getMask();
    int hashindex = hashcode(mask, rel->getKeySize(), RELCACHE_HASHSIZE);
    rel->setHashNext(hash[hashindex]);
    hash[hashindex] = rel;
    return true;
}


//-- findRelation - find a relation in the cache.  Null is returned if the given
//-- relation doesn't exist.
class ocRelation *ocRelCache::findRelation(ocKeySegment *mask, int keysize)
{
    int hashindex = hashcode(mask, keysize, RELCACHE_HASHSIZE);
    ocRelation *rp = hash[hashindex];
    while (rp && ocKey::compareKeys(rp->getMask(), mask, keysize) != 0) rp = rp->getHashNext();
    return rp;	// either NULL, or the matching one
}


//-- dump - print out all relations in the cache
void ocRelCache::dump()
{
    printf("\nDumping RelCache:\n");
    for (int i = 0; i < RELCACHE_HASHSIZE; i++) {
	if (hash[i]) {
	    printf ("hash chain [%d]:\n", i);
	    for (ocRelation *rel = hash[i]; rel; rel = rel->getHashNext()) {
		rel->dump();
	    }
	}
    }
}

