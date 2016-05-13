#ifndef ___Table
#define ___Table

#include "Globals.h"
#include <stdlib.h>

/*
 * Table - defines a data table, which is a collection of tuples. The tuples are stored
 * in a contiguous table.  Since tuples are variable sized, the Table object stores the
 * size information for the tuple storage.
 */

class Relation;

class Table {
    public:
        Table(int keysz, long long maxTuples, TableType typ = TableType:: InformationTheoretic); // initialize the table and allocate tuple space
        ~Table();
        long long size();

        void copy(const Table *from); // copy data table

        //-- add or sum tuples in the table.  These take into account the type of table
        //-- (info theoretic or set theoretic)
        void addTuple(KeySegment *key, double value); // append to end
        void insertTuple(KeySegment *key, double value, long long index); // insert in given spot
        void sumTuple(KeySegment *key, double value); // add (or) this value to matching tuple

        //-- key and value access functions
        double getValue(long long index);
        void setValue(long long index, double value);
        KeySegment *getKey(long long index);
        void copyKey(long long index, KeySegment *key);

        //-- find the given key. If matchOnly is true, -1 is returned on no match.
        //-- if matchOnly is false, the position of the next higher tuple is returned
        long long indexOf(KeySegment *key, bool matchOnly = true); //
        long long getTupleCount() {
            return tupleCount;
        }
        int getKeySize() {
            return keysize;
        }

        void sort(); // sort tuples by key
        void reset(int keysize); // reset table to empty, but reuse the storage

        // dump debug output
        void dump(bool detail = false);

        // normalize information-theoretic table.  No effect for set-theoretic tables.
        // if these are counts, then the return value is the sample size
        double normalize();

        // Add a constant to every value in the table.
        // This is used for function data, and it assumes that the table is fully specified.
        // i.e., it doesn't create missing tuples with assumed zero values, to add the constant to.
        void addConstant(double constant);

        // Returns the lowest value in the table.
        double getLowestValue();

    private:
        void* data; // storage for all keys and values
        int keysize; // number of key segments in the key for each tuple
        long long tupleCount; // number of tuples in the tuple array
        long long maxTupleCount; // the total size of the data member, in terms of tuples
        TableType type; // one of INFO_TYPE, SET_TYPE
};

template <typename F>
void tableIteration(Table* input_table, VariableList* varlist, Relation* rel,
                    Table* fit_table, long var_count, F action) {
    long long dataCount = input_table->getTupleCount();
    int *key_order = new int[dataCount];
    for (long long i = 0; i < dataCount; i++) { key_order[i] = i; }
    sort_var_list = varlist;
    sort_count = var_count;
    sort_vars = nullptr;
    sort_keys = nullptr;
    sort_table = input_table;
    qsort(key_order, dataCount, sizeof(int), sortKeys);
    if (fit_table == NULL) { fit_table = input_table; }
    for (long long order_i = 0; order_i < dataCount; order_i++) {
        int i = key_order[order_i];
        KeySegment* refkey = input_table->getKey(i);
        double refvalue = input_table->getValue(i);
        long long index = fit_table->indexOf(refkey, true);
        double value = index == -1 ? 0.0 : fit_table->getValue(index);
        action(rel, index, value, refkey, refvalue);
    }
}

template <typename F>
void tableIteration2(Table* input_table1, 
                    VariableList* varlist1, 
                    Relation* rel1, 
                    Table* fit_table1,
                    long var_count1,
                    Table* input_table2,
                    VariableList* varlist2,
                    Relation* rel2,
                    long var_count2,
                    Table* fit_table2,
                    F action) {


    // Get data for table 1
    long long dataCount1 = input_table1->getTupleCount();
    int *key_order1 = new int[dataCount1];
    for (long long i = 0; i < dataCount1; i++) { key_order1[i] = i; }

    // Sort table 1
    sort_var_list = varlist1;
    sort_count = var_count1;
    sort_vars = nullptr;
    sort_keys = nullptr;
    sort_table = input_table1;
    qsort(key_order1, dataCount1, sizeof(int), sortKeys);


    if (fit_table1 == NULL) { fit_table1 = input_table1; }

    // Get data for table 2
    long long dataCount2 = input_table2->getTupleCount();
    int *key_order2 = new int[dataCount2];
    for (long long i = 0; i < dataCount2; i++) { key_order2[i] = i; }

    // Sort table 2
    sort_var_list = varlist2;
    sort_count = var_count2;
    sort_vars = nullptr;
    sort_keys = nullptr;
    sort_table = input_table2;
    qsort(key_order2, dataCount2, sizeof(int), sortKeys);


    if (fit_table2 == NULL) { fit_table2 = input_table2; }


    // Do the actual iteration:
    // For each key in table1:
    //      Find the corresponding key in table2 if it exists.
    //      If not assume 0 value.
    //      Call F on the pair.
    //      
    // For each key in table2:
    //      If the key is in table1: ignore this pair and move on.
    //      Else: assume 0 value for table1.
    //      Call F on the pair.
    //
    for (long long order_i1 = 0; order_i1 < dataCount1; order_i1++) {
        int indexR1 = key_order1[order_i1];
        KeySegment* refkey1 = input_table1->getKey(indexR1);
        double refvalue1 = input_table1->getValue(indexR1);
        long long index1 = fit_table1->indexOf(refkey1, true);

        double value1 = index1 == -1 ? 0.0 : fit_table1->getValue(index1);

        long long index2 = fit_table2->indexOf(refkey1, true);
        long long indexR2 = input_table2->indexOf(refkey1, true);
        double value2 = index2 == -1 ? 0.0 : fit_table2->getValue(index2);
        double refvalue2 = indexR2 == -1 ? 0.0 : input_table2->getValue(indexR2);

        action(1, refkey1, rel1, index1, value1, indexR1, refvalue1, rel2, index2, value2, indexR2, refvalue2);
    }

    for (long long order_i2 = 0; order_i2 < dataCount2; order_i2++) {
        int indexR2 = key_order2[order_i2];
        KeySegment* refkey2 = input_table2->getKey(indexR2);
        
        long long index1 = fit_table1->indexOf(refkey2, true);

        // Tuple not in Table1: assume 0 value for Table1 and proceed
        if (index1 == -1) {
            long long indexR1 = input_table2->indexOf(refkey2, true);
            double refvalue1 = indexR1 == -1 ? 0.0 : input_table1->getValue(indexR1);
            double value1 = 0.0;
            double refvalue2 = input_table2->getValue(indexR2);
            long long index2 = fit_table2->indexOf(refkey2, true);
            
            double value2 = index2 == -1 ? 0.0 : fit_table2->getValue(index2);
            action(2, refkey2, rel1, index1, value1, indexR1, refvalue1, rel2, index2, value2, indexR2, refvalue2);      
        }

        // Tuple in Table1: skip, since we already did this one.
    }
}




#endif
