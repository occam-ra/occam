/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */
#ifndef OCMODELCACHE_H
#define OCMODELCACHE_H

/**
 * ocModelCache.h - defines the model cache.  This provides a way to reuse model
 * objects.
 * the cache matches on the printName for the model, which uniquely identifies the
 * set of relations.
 * There must be a separate model cache for each different problem instance.
 *
 */
#define MODELCACHE_HASHSIZE 1001
class ocModelCache {
public:
	//-- construct an empty relation cache
	ocModelCache();
	
	//-- destroy relation cache.  This also deletes all the models held in the cache.
	~ocModelCache();

	long size();

	//-- addModel - put a new relation in the cache. If a matching model already
	//-- exists, an error is returned.
	bool addModel(class ocModel *model);
	
	//-- findModel - find a model in the cache.  Null is returned if the given
	//-- model doesn't exist.
	class ocModel *findModel(const char *name);
	
	void dump();
	
private:
	class ocModel **hash;
};

#endif


