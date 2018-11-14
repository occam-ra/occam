/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#ifndef ___RelationCache
#define ___RelationCache

/**
 * RelCache.h - defines the relation cache.  This provides a way to reuse relation
 * objects, since once constructed a relation object can be used by any model
 * containing that relation.
 * the cache matches on the mask for the relation, which uniquely identifies the
 * set of variables in the relation.
 * There must be a separate relation cache for each different problem instance.
 *
 */
#define RELCACHE_HASHSIZE 1001
class RelCache {
    public:
	//-- construct an empty relation cache
	RelCache();

	//-- destroy relation cache.  This also deletes all the relations held in the cache.
	~RelCache();

	long size();

	//-- delete projection tables from all relations in cache
	void deleteTables();

	//-- addRelation - put a new relation in the cache. If a matching relation already
	//-- exists, an error is returned.
	bool addRelation(class Relation *rel);

	//-- findRelation - find a relation in the cache.  Null is returned if the given
	//-- relation doesn't exist.
	class Relation *findRelation(const char *name);

	void dump();

    private:
	class Relation **hash;
};

#endif

