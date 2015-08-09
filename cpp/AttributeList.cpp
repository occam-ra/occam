#include "Core.h"
#include "_Core.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "Win32.h"

/**
 * AttributeList.cpp - implements an attribute list, a sequence of name/value
 * pairs attached to another object. Searching by name is supported, as well as
 * iterating over the attributes (get the count, then access by index)
 */

static int findName(const char **names, const char *name, int count)
{
    //-- if name contains "$", everything after that is formatting info, so don't compare that part.
    const char *cp = strchr(name, '$');
    int len = (cp == 0) ? strlen(name) : cp - name;
    char *name2 = new char[len+1];
    strncpy(name2, name, len);
    name2[len] = '\0';
    int match = -1;
    for (int i = 0; i < count; i++) {
	if (strcasecmp(name2, names[i]) == 0) {
	    match = i;
	    break;
	}
    }
    delete [] name2;
    return match;
}


AttributeList::AttributeList(int size)
{
    attrCount = 0;
    maxAttrCount = size;
    names = new const char*[maxAttrCount];
    values = new double[maxAttrCount];
    memset(names,0,maxAttrCount*sizeof(char));
    memset(values,0,maxAttrCount*sizeof(double));
}


AttributeList::~AttributeList()
{
    if (names) delete [] names;
    if (values) delete [] values;
}


long AttributeList::size()
{
    return sizeof(AttributeList) * maxAttrCount * (sizeof(char*) + sizeof(double));
}


void AttributeList::reset()
{
    attrCount = 0;
}


void AttributeList::setAttribute(const char *name, double value)
{
    const int FACTOR = 2;

    // if this attribute is already in the list, change it;
    // otherwise, add a new one
    int index = findName(names, name, attrCount);
    if (index >= 0) values[index] = value;
    else {
	while (attrCount >= maxAttrCount) {
	    names = (const char **) growStorage(names, maxAttrCount*sizeof(char*), FACTOR);
	    values = (double*) growStorage(values, maxAttrCount*sizeof(double), FACTOR);
	    maxAttrCount *=	FACTOR;
	}
	names[attrCount] = name;
	values[attrCount++] = value;
    }
}


int AttributeList::getAttributeIndex(const char *name)
{
    return findName(names, name, attrCount);
}


double AttributeList::getAttribute(const char *name)
{
    int index = findName(names, name, attrCount);
    return (index >= 0) ? values[index] : -1.0;
}


int AttributeList::getAttributeCount()
{
    return attrCount;
}


double AttributeList::getAttributeByIndex(int index)
{
    return (index < attrCount) ? values[index] : -1.0;
}


void AttributeList::dump()
{
    if (attrCount == 0) return;
    printf("\t\tAttributes: %d/%d", attrCount, maxAttrCount);
    //for (int i = 0; i < attrCount; i++) {
    //printf("\t%s: %lf", names[i], values[i]);
    //}
}

