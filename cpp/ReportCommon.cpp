#include "Report.h"
#include <cstring>
#include "ManagerBase.h"
void Report::newl(FILE* fd) {
    if (htmlMode) {
        fprintf(fd, "<br/>");
    }
    fprintf(fd, "\n");
}

void Report::hl(FILE* fd) {
    if (htmlMode) {
        fprintf(fd, "<hr/>");
    }
    newl(fd);
}

int Report::sepStyle() { return htmlMode ? 0 : separator; }

const char* format_arr[] = {
    "%s<td>%s|</td><td>%#6.8g</td><td>%#6.8g</td><td>|</td><td>%#6.8g</td><td>%#6.8g</td><td>%+#6.8g</td></tr>\n",
    "%s%s|\t%#6.8g\t%#6.8g\t|\t%#6.8g\t%#6.8g\t%#6.8g\n",
    "%s%s|,%#6.8g,%#6.8g,|,%#6.8g,%#6.8g,%#6.8g\n",
    "%s%8s|  %#6.8g   %#6.8g   |   %#6.8g   %#6.8g   %#6.8g\n"
};

const char* format_r_arr[] = {
    "%s<td>%s|</td><td>%#6.8g</td><td>%#6.8g</td></tr>\n",
    "%s%s|\t%#6.8g\t%#6.8g\n",
    "%s%s|,%#6.8g,%#6.8g\n",
    "%s%8s|  %#6.8g   %#6.8g\n"
};

const char* format_l_arr[] = {
    "%s<td>%s|</td><td>%#6.8g</td><td>%#6.8g</td><td>|</td><td>%#6.8g</td><td>%#6.8g</td><td>%+#6.8g</td><td>|</td><td>%#6.8g</td></tr>\n",
    "%s%s|\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\n",
    "%s%s|,%#6.8g,%#6.8g,%#6.8g,%#6.8g,%#6.8g,%#6.8g\n",
    "%s%8s|  %#6.8g   %#6.8g   %#6.8g   %#6.8g   %#6.8g    %#6.8g\n"
};

const char* format_lr_arr[] = {
    "%s<td>%s|</td><td>%#6.8g</td><td>%#6.8g</td><td>|</td><td>%#6.8g</td></tr>\n",
    "%s%s\t|\t%#6.8g\t%#6.8g\t%#6.8g\n",
    "%s%s,|,%#6.8g,%#6.8g,%#6.8g\n",
    "%s%8s  |  %#6.8g   %#6.8g    %#6.8g\n"
};

const char* footer_arr[] = {
    "</table><br><br>",
    "",
    "",
    ""
};

const char* delim_arr[] = {
    "</td><td>",
    "\t",
    ",",
    " "
};

const char* hdr_delim_arr[] = {
    "</th><th>",
    "\t",
    ",",
    " "
};

const char* header_start[] = {
    "<table cellspacing=0 cellpadding=0><tr><th>",
    "",
    "",
    ""
};

const char* header_cont[] = {
    "Obs.Prob.</th><th>Obs.Freq.",
    "Obs.Prob.\tObs.Freq.",
    "Obs.Prob.,Obs.Freq.",
    "Obs.Prob.    Obs.Freq."
};

const char* header_finish[] = {
    "</th></tr>\n",
    "\n",
    "\n",
    "\n"
};

void Report::header(FILE* fd, Relation* rel, bool printLift, bool printCalc) { 

    fprintf(fd, "%s", header_start[sepStyle()]);
    VariableList* var_list = manager->getVariableList();
    int var_count = var_list->getVarCount(); 
    if (rel) {

        int *ind_vars = new int[var_count];
        int iv_count = rel->getIndependentVariables(ind_vars, var_count);
        for (int i = 0; i < iv_count; i++)
            fprintf(fd, "%s%s", var_list->getVariable(ind_vars[i])->abbrev, hdr_delim());
    } else {
        for (int i = 0; i < var_count; i++) {
            fprintf(fd, "%s%s", var_list->getVariable(i)->abbrev, hdr_delim());
        }
    }

    fprintf(fd, "|%s%s", hdr_delim(), header_cont[sepStyle()]);

    if (printCalc) {
        fprintf(fd, "%s|%sCalc.Prob.%sCalc.Freq.%sResidual", hdr_delim(), hdr_delim(), hdr_delim(), hdr_delim());   
    }
    if (printLift) {
        fprintf(fd, "%s|%sLift", hdr_delim(), hdr_delim(), hdr_delim());
    }
    fprintf(fd, "%s", header_finish[sepStyle()]);
}

const char* Report::format(bool printLift, bool printCalc) { 
    return printLift 
        ? (printCalc ? format_l_arr[sepStyle()] : format_lr_arr[sepStyle()])
        : (printCalc ? format_arr[sepStyle()] : format_r_arr[sepStyle()]); 
}

void Report::footer(FILE* fd) { fprintf(fd, "%s", footer_arr[sepStyle()]); }
const char* Report::delim() { return delim_arr[sepStyle()]; }
const char* Report::hdr_delim() { return hdr_delim_arr[sepStyle()]; }


void Report::printTableRow(FILE* fd, bool blue, VariableList* varlist, int var_count, Relation* rel, double value, KeySegment* refkey, double refvalue, double indep_value, double adjustConstant, double sample_size, bool printLift, bool printCalc) {
    char* keystr = new char[var_count * (MAXABBREVLEN + strlen(delim())) + 1];
    Key::keyToUserString(refkey, varlist, keystr, delim());

    const char* pre = !htmlMode ? "" : (blue ? "<tr class=r1>" : "<tr>");
    const char* fmt = format(printLift, rel == NULL || printCalc);
    double lift = value / indep_value;

    if (rel == NULL || printCalc) {
        double res = value - refvalue;
        if (printLift) {

            fprintf(fd, fmt, pre, keystr, refvalue, refvalue * sample_size - adjustConstant, value, value * sample_size - adjustConstant, res, lift);
        } else {

            fprintf(fd, fmt, pre, keystr, refvalue, refvalue * sample_size - adjustConstant, value, value * sample_size - adjustConstant, res);
        }

    } else if(rel != NULL) { 
        if (printLift) {
            fprintf(fd, fmt, pre, keystr, refvalue, refvalue * sample_size - adjustConstant, lift); 

        } else {
            fprintf(fd, fmt, pre, keystr, refvalue, refvalue * sample_size - adjustConstant); 
        }
    }
    delete[] keystr;
}

void Report::printTable(FILE* fd, Relation* rel, Table* fit_table, Table* input_table, Table* indep_table, double adjustConstant, double sample_size, bool printLift, bool printCalc) {

    
    VariableList* varlist = rel ? rel->getVariableList() : manager->getVariableList();
    int var_count = varlist->getVarCount();
    header(fd, rel, printLift, printCalc);
    bool blue = 1;

    auto tableAction = [&](Relation* rel, double value, KeySegment* refkey, double refvalue, double iviValue) {

        printTableRow(fd, blue, varlist, var_count, rel, value, refkey, refvalue, iviValue, adjustConstant, sample_size, printLift, printCalc);
        blue = !blue;
    };

    tableIteration(input_table, varlist, rel, fit_table, indep_table, var_count, tableAction);
    
    footer(fd);
}
