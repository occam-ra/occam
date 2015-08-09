#include "Core.h"
#include "_Core.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const long long GROWTH_FACTOR = 2;


/*
 * Table - initialize the table. The given keysize and number of tuples are used
 * to allocate storage.  The max number of tuples can be changed after creation, but
 * the keysize cannot.
 *
 * The data storage consists of {[keyseg 0]..[keyseg n][value]}..., in a contiguous
 * array. The macros below provide indexed access to this storage. Note that in order
 * for quicksort to work, the key must be first
 */

#define TupleBytes (sizeof(ocTupleValue) + keysize * sizeof(KeySegment))


static ocTupleValue *ValuePtr(void *data, int keysize, long long index)
{
    return ((ocTupleValue*) ( ((char*) data) + (keysize * sizeof(KeySegment)) + TupleBytes * (index) ));
}


static KeySegment *KeyPtr(void *data, int keysize, long long index)
{
    return ((KeySegment*) ( ((char*) data) + TupleBytes * (index) ));
}


Table::Table(int keysz, long long maxTuples, TableType typ)
{
    keysize = keysz;
    type = typ;
    maxTupleCount = maxTuples;
    tupleCount = 0;
    data = new char[TupleBytes * maxTuples];
    memset(data, 0, TupleBytes * maxTuples * sizeof(char));
}


Table::~Table()
{
    if (data) delete [] (char*)data;
}


long long Table::size()
{
    return TupleBytes * maxTupleCount + sizeof(Table);
}


void Table::copy(const Table* from)
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
void Table::addTuple(KeySegment *key, double value)
{
    while (tupleCount >= maxTupleCount) {
        data = growStorage(data, maxTupleCount*TupleBytes, GROWTH_FACTOR);
        maxTupleCount *= GROWTH_FACTOR;
    }
    KeySegment *keyptr = KeyPtr(data, keysize, tupleCount);
    memcpy(keyptr, key, sizeof(KeySegment) * keysize);			// copy key
    //-- for set relations, only values are 1 or 0
    if (type == TableType::SetTheoretic && value != 0.0) value = 1.0;
    *(ValuePtr(data, keysize, tupleCount)) = (ocTupleValue) value;		// copy value
    tupleCount++;
}


/**
 * insertTuple - similar to addTuple, but inserts the tuple in sorted order.
 */
void Table::insertTuple(KeySegment *key, double value, long long index)
{
    while (tupleCount >= maxTupleCount) {
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

    KeySegment *keyptr = KeyPtr(data, keysize, index);
    memcpy(keyptr, key, sizeof(KeySegment) * keysize);	// copy key
    //-- for set relations, only values are 1 or 0
    if (type == TableType::SetTheoretic && value != 0.0) value = 1.0;
    *(ValuePtr(data, keysize, index)) = (ocTupleValue) value;						// copy value
    tupleCount++;
}


/**
 * sumTuple - if the tuple matching the key already exists, add this value
 * to it.  If not, add a new Tuple.
 */
void Table::sumTuple(KeySegment *key, double value)
{
    long long index = indexOf(key, false);
    //-- index is either the matching tuple, or the next higher one. So we have to test again.
    if (index >= tupleCount || Key::compareKeys(KeyPtr(data, keysize, index), key, keysize) != 0) {
        insertTuple(key, value, index);
    } else {
        ocTupleValue *valuep = ValuePtr(data, keysize, index);
        value += *valuep;
        if (type == TableType::SetTheoretic && value != 0.0) value = 1.0;
        *valuep = (ocTupleValue) value;
    }
}


/**
 * getValue - return the value at a given index.  If the index is negative, return
 * 0 as the value (a negative index by convention means the tuples does not exist in
 * the table, so zero is the correct return value).
 */
double Table::getValue(long long index)
{
    if (index < 0 || index >= tupleCount) return 0.0;
    return (double) *(ValuePtr(data, keysize, index));
}


/**
 * setValue - set the value at the given index
 */
void Table::setValue(long long index, double value)
{
    if ((index < 0) || (index >= tupleCount)) return;
    else *(ValuePtr(data, keysize, index)) = (ocTupleValue) value;
}


/**
 * getKey - similar to getValue
 */
KeySegment *Table::getKey(long long index)
{
    if (index < 0 || index >= tupleCount) return 0;
    else return KeyPtr(data, keysize, index);
}


/**
 * copyKey - copy the key into the caller's storage
 */
void Table::copyKey(long long index, KeySegment *key)
{
    KeySegment *keyp = getKey(index);
    memcpy(key, keyp, keysize*sizeof(KeySegment));
}


/**
 * indexOf - search the table for the given key, and return the index. Returns -1 if not
 * found. This function assumes the keys are sorted, and does a binary search.
 */
long long Table::indexOf(KeySegment *key, bool matchOnly)
{
    int compare;
    long long top = 0;
    long long bottom = tupleCount - 1;
    if (bottom < 0) return matchOnly ? -1 : 0;	// empty table

    // Handle ends of range first
    compare = Key::compareKeys(KeyPtr(data, keysize, top), key, keysize);
    if (compare == 0) return top;
    else if (compare > 0) return matchOnly ? -1 : 0;

    compare = Key::compareKeys(KeyPtr(data, keysize, bottom), key, keysize);
    if (compare == 0) return bottom;
    else if (compare < 0) return matchOnly ? -1 : tupleCount;

    if ((bottom - top) <= 1) return matchOnly ? -1 : bottom;	// no range left to search
    long long mid = bottom / 2;
    // Now loop until we either run out of room to search, or find a match.
    // Each iteration, the midpoint of the remaining range is checked, and
    // then half the keys are discarded.
    while (true) {
        compare = Key::compareKeys(KeyPtr(data, keysize, mid), key, keysize);
        if (compare == 0) return mid;	// got a match
        if (compare > 0) {	// search top half of range
            bottom = mid;
        } else {	// search bottom half of range
            top = mid;
        }
        if ((bottom - top) <= 1) return matchOnly ? -1 : bottom;	// no range left to search
        mid = (bottom + top) / 2;
    }
    return -1;	// this is never reached
}


/**
 * sort() - sort the tuples by key value (to allow binary search).  This uses
 * the Unix QuickSort function qsort. We need a little adaptor function for the
 * comparator, because compareKeys isn't quite right
 */
static int sortKeySize;	// must be set before calling sortCompare
static int sortCompare(const void *k1, const void *k2)
{
    return Key::compareKeys((KeySegment *)k1, (KeySegment *)k2, sortKeySize);
}


void Table::sort()
{
    sortKeySize = keysize;
    qsort(data, tupleCount, TupleBytes, sortCompare);
}


/**
 * normalize - normalize values to sum to 1.0
 */
double Table::normalize()
{
    double denom = 0;
    long long i;
    for (i = 0; i < tupleCount; i++) {
        denom += getValue(i);
    }
    for (i = 0; i < tupleCount; i++) {
        setValue(i, (getValue(i)/denom));
    }
    //-- if the data was already normalized, then not much will have happened.
    //-- but in that case there is no sample size info, so return 1.
    //if (denom < 1.5) return 1;
    //else return denom;
    return denom;
}


// Adds a constant to every value in the table.
void Table::addConstant(double constant)
{
    long long i;
    for (i = 0; i < tupleCount; i++) {
        setValue(i, getValue(i) + constant);
    }
}


// Returns the lowest value in the table.
double Table::getLowestValue()
{
    double lowest = getValue(0);
    for (long long i = 0; i < tupleCount; i++) {
        if (getValue(i) < lowest)
            lowest = getValue(i);
    }
    return lowest;
}


/**
 * reset - reset table to empty
 */
void Table::reset(int keysize)
{
    this->tupleCount = 0;
    this->keysize = keysize;
}


/**
 * dump() - dump debug output
 */
void Table::dump(bool detail)
{
    double sum = 0;
    printf("Table: tuples = %lld<br>", tupleCount);
    for (long long i = 0; i < tupleCount; i++) {
        KeySegment *key = getKey(i);
        double value = getValue(i);
        if (detail) {
            printf("\t%d. ", i);
            Key::dumpKey(key, keysize);
            printf("%g<br>", value);
        }
        sum += value;
    }
    printf("p total (should be 1.00): %lg<br>", sum);
}

