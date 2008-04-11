/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

/**
 * ocTable.cpp - implements the Table class.  A Table consists logically of a list of tuples.
 * In this implementation, the table contains an array of keys (the value part of each
 * tuple) and a separate array of values, all indexed with the same index.
 */
 
 #include "ocCore.h"
 #include "_ocCore.h"
 #include <assert.h>
 #include <stdio.h>
 #include <stdlib.h>
 #include <string.h>
 
const long GROWTH_FACTOR = 2;

 
 /*
  * ocTable - initialize the table. The given keysize and number of tuples are used
  * to allocate storage.  The max number of tuples can be changed after creation, but
  * the keysize cannot.
  *
  * The data storage consists of {[keyseg 0]..[keyseg n][value]}..., in a contiguous
  * array. The macros below provide indexed access to this storage. Note that in order
  * for quicksort to work, the key must be first
  */

#define TupleBytes (sizeof(ocTupleValue) + keysize * sizeof(ocKeySegment))

static ocTupleValue *ValuePtr(void *data, int keysize, long long index)
{
	return ((ocTupleValue*) ( ((char*) data) + (keysize * sizeof(ocKeySegment)) + TupleBytes * (index) ));
}

static ocKeySegment *KeyPtr(void *data, int keysize, long long index)
{
	return ((ocKeySegment*) ( ((char*) data) + TupleBytes * (index) ));
}

ocTable::ocTable(int keysz, long long maxTuples, ocTable::TableType typ)
{
 	keysize = keysz;
	type = typ;
	maxTupleCount = maxTuples;
	tupleCount = 0;
	data = new char[TupleBytes * maxTuples];
}

ocTable::~ocTable()
{
	if (data) delete [] (char*)data;
}

long long ocTable::size()
{
	return TupleBytes * maxTupleCount + sizeof(ocTable);
}

void ocTable::copy(const ocTable* from)
{
	while (from->tupleCount > maxTupleCount) {
		data = growStorage(data, maxTupleCount*TupleBytes, GROWTH_FACTOR);
		maxTupleCount *= GROWTH_FACTOR;
	}
	memcpy(data, from->data, TupleBytes * maxTupleCount);
	tupleCount = from->tupleCount;
}

/**
 * addTuple - append a tuple to the table. The variable length key is copied to the key store,
 * and the value to the value store.  The table is resized if needed.
 */
void ocTable::addTuple(ocKeySegment *key, double value)
{
	if (tupleCount >= maxTupleCount) {
		data = growStorage(data, maxTupleCount*TupleBytes, GROWTH_FACTOR);
		maxTupleCount *= GROWTH_FACTOR;
	}
	ocKeySegment *keyptr = KeyPtr(data, keysize, tupleCount);
	memcpy(keyptr, key, sizeof(ocKeySegment) * keysize);			// copy key
	//-- for set relations, only values are 1 or 0
	if (type == SET_TYPE && value != 0.0) value = 1.0;
	*(ValuePtr(data, keysize, tupleCount)) = (ocTupleValue) value;		// copy value
	tupleCount++;
}

/**
 * insertTuple - similar to addTuple, but inserts the tuple in sorted order.
 */
void ocTable::insertTuple(ocKeySegment *key, double value, long long index)
{
	if (tupleCount >= maxTupleCount) {
		data = growStorage(data, maxTupleCount*TupleBytes, GROWTH_FACTOR);
		maxTupleCount *= GROWTH_FACTOR;
	}
	if (index < tupleCount) {
		void* dest = KeyPtr(data, keysize, index + 1);
		void* src = KeyPtr(data, keysize, index);
		long size = ((char*)KeyPtr(data, keysize, tupleCount)) - ((char*)KeyPtr(data, keysize, index));
		memmove(dest, src, size);
	}
	// else?
	
	ocKeySegment *keyptr = KeyPtr(data, keysize, index);
	memcpy(keyptr, key, sizeof(ocKeySegment) * keysize);	// copy key
	//-- for set relations, only values are 1 or 0
	if (type == SET_TYPE && value != 0.0) value = 1.0;
	*(ValuePtr(data, keysize, index)) = (ocTupleValue) value;						// copy value
	tupleCount++;
}


/**
 * sumTuple - if the tuple matching the key already exists, add this value
 * to it.  If not, add a new Tuple.
 */
void ocTable::sumTuple(ocKeySegment *key, double value)
{
	long long index = indexOf(key, false);
	//-- index is either the matching tuple, or the next higher one. So we have to
	//-- test again.
	if (index >= tupleCount || ocKey::compareKeys(KeyPtr(data, keysize, index), key, keysize) != 0) {
		insertTuple(key, value, index);
	}
	else {
		ocTupleValue *valuep = ValuePtr(data, keysize, index);
		value += *valuep;
		if (type == SET_TYPE && value != 0.0) value = 1.0;
		*valuep = (ocTupleValue) value;
	}
}


/**
 * getValue - return the value at a given index.  If the index is negative, return
 * 0 as the value (a negative index by convention means the tuples does not exist in
 * the table, so zero is the correct return value).
 */
double ocTable::getValue(long long index)
{
	if (index < 0 || index >= tupleCount) return 0.0;
	else return (double) *(ValuePtr(data, keysize, index));
}

/**
 * setValue - set the value at the given index
 */
void ocTable::setValue(long long index, double value)
{
	if (index < 0 || index >= tupleCount) return;
	else *(ValuePtr(data, keysize, index)) = (ocTupleValue) value;
}


/**
 * getKey - similar to getValue
 */
ocKeySegment *ocTable::getKey(long long index)
{
	if (index < 0 || index >= tupleCount) return 0;
	else return KeyPtr(data, keysize, index);
}

/**
 * copyKey - copy the key into the caller's storage
 */
void ocTable::copyKey(long long index, ocKeySegment *key)
{
	ocKeySegment *keyp = getKey(index);
	memcpy(key, keyp, keysize*sizeof(ocKeySegment));
}

/**
 * indexOf - search the table for the given key, and return the index. Returns -1 if not
 * found. This function assumes the keys are sorted, and does a binary search.
 */
long long ocTable::indexOf(ocKeySegment *key, bool matchOnly)
{
	int compare;
	long long top = 0, bottom = tupleCount - 1;
	if (bottom < 0) return matchOnly ? -1 : 0;	// empty table
	// handle ends of range first
	compare = ocKey::compareKeys(KeyPtr(data, keysize, top), key, keysize);
	if (compare > 0) return matchOnly ? -1 : 0;
	else if (compare == 0) return top;
	
	compare = ocKey::compareKeys(KeyPtr(data, keysize, bottom), key, keysize);
	if (compare < 0) return matchOnly ? -1 : tupleCount;
	else if (compare == 0) return bottom;
	
	// now loop until we either run out of room to search, or find a match.
	// each iteration, the midpoint of the remaining range is checked, and
	// then half the keys are discarded.
	while (true) {
		if (bottom - top <= 1) return matchOnly ? -1 : bottom;	// no range left to search
		long long mid = (bottom + top) / 2;
		compare = ocKey::compareKeys(KeyPtr(data, keysize, mid), key, keysize);
		if (compare == 0) return mid;	// got a match
		if (compare > 0) {	// search top half of range
			bottom = mid;
		} else {	// search bottom half of range
			top = mid;
		}
	}
	return -1;	// this is never reached
}

/**
 * sort() - sort the tuples by key value (to allow binary search).  This uses
 * the Unix QuickSort function qsort. We need a little adaptor function for the
 * comparitor, because compareKeys isn't quite right
 */
static int sortKeySize;	// must be set before calling sortCompare
static int sortCompare(const void *k1, const void *k2)
{
	return ocKey::compareKeys((ocKeySegment *)k1, (ocKeySegment *)k2, sortKeySize);
}

void ocTable::sort()
{
	sortKeySize = keysize;
	qsort(data, tupleCount, TupleBytes, sortCompare);
}

/**
 * normalize - normalize values to sum to 1.0
 */
int ocTable::normalize()
{
	double denom = 0;
	long long count = getTupleCount();
	long long i;
	for (i = 0; i < count; i++) {
		denom += getValue(i);
	}
	for (i = 0; i < count; i++) {
		setValue(i, (getValue(i)/denom));
	}
	//-- if the data was already normalized, then not much will have happened.
	//-- but in that case there is no sample size info, so return 1.
	if (denom < 1.5) return 1;
	else return (int) denom;
}

/**
 * getMaxValue - get the index of the tuple with the greatest value
 */
long long ocTable::getMaxValue()
{
	double maxv = 0;
	long long maxi = -1;
	long long count = getTupleCount();
	long long i;
	for (i = 0; i < count; i++) {
		double value = getValue(i);
		if (value > maxv) {
			maxv = value;
			maxi = i;
		}
	}
	return maxi;
}

/**
 * reset - reset table to empty
 */
void ocTable::reset(int keysize)
{
	this->tupleCount = 0;
	this->keysize = keysize;
}

/**
 * dump() - dump debug output
 */
void ocTable::dump(bool detail)
{
	double sum = 0;
	printf("ocTable: tuples = %ld\n", tupleCount);
	for (long long i = 0; i < tupleCount; i++) {
		ocKeySegment *key = getKey(i);
		double value = getValue(i);
		if (detail) {
			printf("\t");
			for (int k = 0; k < keysize; k++) {
				printf("%08lx ", key[k]);
			}
			printf("%g\n", value);
		}
		sum += value;
	}
	printf("p total (should be 1.00): %lg\n", sum);
}

