ocVBMManager:
	ATTRIBUTES

	FUNCTIONS
	void initFromCommandLine()
		Read command line arguments, and any data files defined by them,
		and set options.

	ocRelation[] makeAllChildRelations(ocRelation, bool makeProject)
		Make all the child relations of a given relation and place them
		in the relation cache. If makeProject is true, create projection
		tables for all relations

	ocModel makeChildModel(ocModel, int relation, bool makeProjection)
		Make a child model of the given model, by replacing the relation
		given (by ordinal position) with its embedded relations. If
		makeProjection is true, create data tables for the relations

	ocModel getTopRefModel()
		Returns the top model.

	double computeDF(ocModel)
		Computes df for the given model.

	double computeH(ocModel)
		Computes H for the given model. This uses IPF automatically if
		the model has loops. Computations is skipped if H has already
		been computed for this model.

	double computeT(ocModel)
		Computes T for the given model. This uses IPF automatically if
		the model has loops. Computation is skipped if H has already
		been computed for this model.

ocRelation
	ATTRIBUTES
		name - returns the name of the relation in canonical form
		varcount - returns the number of variables in the relation

	FUNCTIONS
	double get(string attributeName)
		Return the indicated attribute, performing whatever computations
		are needed.

ocModel
	ATTRIBUTES
		name - returns the name of the model in canonical form
		relcount - returns the number of relations in the model

	FUNCTIONS
	double get(string attributeName)
		Return the indicated attribute, performing whatever computations
		are needed.
	ocRelation getRelation(int index)
		Return the relation at the given ordinal position.