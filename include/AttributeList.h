#ifndef ___AttributeList
#define ___AttributeList

/**
 * AttributeList - associated with models and relations, an attribute carries a name and a numeric value.
 */
class AttributeList {
    public:
        // initialize empty attribute list
        AttributeList(int size);
        ~AttributeList();
        long size();
        void reset();

        // Add an attribute. Names are not copied so the name argument must point to a
        // permanent string. If an attribute by this name already exists, it is replaced.
        void setAttribute(const char *name, double value);
        double getAttribute(const char *name);
        int getAttributeIndex(const char *name);
        int getAttributeCount();
        double getAttributeByIndex(int index);

        // Print out values
        void dump();

    private:
        const char** names;
        double *values;
        int attrCount;
        int maxAttrCount;
};

#endif
