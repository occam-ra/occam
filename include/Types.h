/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#ifndef ___Types
#define ___Types

//-- typedef for constructing data keys - defined as a 32-bit type. A key consists
//-- of an array of key segments.  Variable values are packed together into the key
//-- but don't cross segment boundaries. For example, 16 3-state variables can be
//-- packed into one key segment.

typedef unsigned long KeySegment;
typedef double ocTupleValue;
enum class Direction { Ascending, Descending };
enum class TableType { InformationTheoretic, SetTheoretic };

#endif
