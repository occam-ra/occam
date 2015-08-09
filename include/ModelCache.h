#ifndef OCMODELCACHE_H
#define OCMODELCACHE_H

/**
 * ModelCache.h - defines the model cache.  This provides a way to reuse model
 * objects.
 * the cache matches on the printName for the model, which uniquely identifies the
 * set of relations.
 * There must be a separate model cache for each different problem instance.
 *
 */
#define MODELCACHE_HASHSIZE 1001
class ModelCache {
    public:
	//-- construct an empty model cache
	ModelCache();

	//-- destroy model cache.  This also deletes all the models held in the cache.
	~ModelCache();

	long size();

	//-- addModel - put a new model in the cache. If a matching model already
	//-- exists, an error is returned.
	bool addModel(class Model *model);

	//-- deleteModel - deletes a model from the cache.
	//-- returns true if successful, false if not found.
	bool deleteModel(class Model *model);

	//-- findModel - find a model in the cache.  Null is returned if the given
	//-- model doesn't exist.
	class Model *findModel(const char *name);

	void dump();

    private:
	class Model **hash;
};

#endif


