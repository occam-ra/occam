//-- Some definitions to bridge between gcc and Visual Studio

#ifndef OCWIN32_H
#define OCWIN32_H


#ifdef WIN32

#define M_LN2 log(2.0)

#define strcasecmp(str1, str2) stricmp(str1, str2)

#endif /* WIN32 */

#endif /* OCWIN32_H */


