/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */
#ifndef OCRELCACHE_H
#define OCRELCACHE_H

/**
 * ocRelCache.h - defines the relation cache.  This provides a way to reuse relation
 * objects, since once constructed a relation object can be used by any model
 * containing that relation.
 * the cache matches on the mask for the relation, which uniquely identifies the
 * set of variables in the relation.
 * There must be a separate relation cache for each different problem instance.
 *
 */
#define RELCACHE_HASHSIZE 1001
class ocRelCache {
    public:
	//-- construct an empty relation cache
	ocRelCache();

	//-- destroy relation cache.  This also deletes all the relations held in the cache.
	~ocRelCache();

	long size();

	//-- delete projection tables from all relations in cache
	void deleteTables();

	//-- addRelation - put a new relation in the cache. If a matching relation already
	//-- exists, an error is returned.
	bool addRelation(class ocRelation *rel);

	//-- findRelation - find a relation in the cache.  Null is returned if the given
	//-- relation doesn't exist.
	class ocRelation *findRelation(ocKeySegment *mask, int keysize);

	void dump();

    private:
	class ocRelation **hash;
};

#endif

