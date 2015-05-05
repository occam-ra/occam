VBMManager:
	ATTRIBUTES

	FUNCTIONS
	void initFromCommandLine()
		Read command line arguments, and any data files defined by them,
		and set options.

	Relation[] makeAllChildRelations(Relation, bool makeProject)
		Make all the child relations of a given relation and place them
		in the relation cache. If makeProject is true, create projection
		tables for all relations

	Model makeChildModel(Model, int relation, bool makeProjection)
		Make a child model of the given model, by replacing the relation
		given (by ordinal position) with its embedded relations. If
		makeProjection is true, create data tables for the relations

	Model getTopRefModel()
		Returns the top model.

	double computeDF(Model)
		Computes df for the given model.

	double computeH(Model)
		Computes H for the given model. This uses IPF automatically if
		the model has loops. Computations is skipped if H has already
		been computed for this model.

	double computeT(Model)
		Computes T for the given model. This uses IPF automatically if
		the model has loops. Computation is skipped if H has already
		been computed for this model.

Relation
	ATTRIBUTES
		name - returns the name of the relation in canonical form
		varcount - returns the number of variables in the relation

	FUNCTIONS
	double get(string attributeName)
		Return the indicated attribute, performing whatever computations
		are needed.

Model
	ATTRIBUTES
		name - returns the name of the model in canonical form
		relcount - returns the number of relations in the model

	FUNCTIONS
	double get(string attributeName)
		Return the indicated attribute, performing whatever computations
		are needed.
	Relation getRelation(int index)
		Return the relation at the given ordinal position.