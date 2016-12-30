#include "Report.h"
#include <cstring>
#include "ManagerBase.h"
#include <math.h>
#include "Constants.h"

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
    "%s<td>%s|</td><td>%#6.8g</td><td>%#6.8g</td><td>|</td><td>%#6.8g</td><td>%#6.8g</td><td>%+#6.8g</td><td>|</td><td>%#6.8g</td><td>%#6.8g</td><td>%#6.8g</td></tr>\n",
    "%s%s|\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\n",
    "%s%s|,%#6.8g,%#6.8g,%#6.8g,%#6.8g,%#6.8g,%#6.8g,%#6.8g,%#6.8g\n",
    "%s%8s|  %#6.8g   %#6.8g   %#6.8g   %#6.8g   %#6.8g    %#6.8g    %#6.8g    %#6.8g\n"
};

const char* format_lr_arr[] = {
    "%s<td>%s|</td><td>%#6.8g</td><td>%#6.8g</td><td>|</td><td>%#6.8g</td><td>%#6.8g</td><td>%#6.8g</td></tr>\n",
    "%s%s\t|\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\n",
    "%s%s,|,%#6.8g,%#6.8g,%#6.8g,%#6.8g,%#6.8g\n",
    "%s%8s  |  %#6.8g   %#6.8g    %#6.8g    %#6.8g    %#6.8g\n"
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

const char* row_start[] = {
    "<tr><th>",
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

void Report::header(FILE* fd, Relation* rel, bool printLift, bool printCalc, bool printStart) { 
    fprintf(fd, "%s", printStart ? header_start[sepStyle()] : row_start[sepStyle()]); 
    VariableList* var_list = manager->getVariableList();
    int var_count = var_list->getVarCount(); 
    const auto hdr = hdr_delim();
    if (rel) {

        int *ind_vars = new int[var_count];
        int iv_count = rel->getIndependentVariables(ind_vars, var_count);
        for (int i = 0; i < iv_count; i++)
            fprintf(fd, "%s%s", var_list->getVariable(ind_vars[i])->abbrev, hdr);
    } else {
        for (int i = 0; i < var_count; i++) {
            fprintf(fd, "%s%s", var_list->getVariable(i)->abbrev, hdr);
        }
    }

    fprintf(fd, "|%s%s", hdr, header_cont[sepStyle()]);

    if (printCalc) {
        fprintf(fd, "%s|%sCalc.Prob.%sCalc.Freq.%sResidual", hdr, hdr, hdr, hdr);   
    }
    if (printLift) {
        
        fprintf(fd, "%s|%sInd.Prob.%sInd.Freq.%sLift", hdr, hdr, hdr, hdr);
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


void Report::printTableRow(FILE* fd, bool blue, VariableList* varlist, int var_count, Relation* rel, double value, KeySegment* refkey, double refvalue, double iviValue, double adjustConstant, double sample_size, bool printLift, bool printCalc) {
    char* keystr = new char[var_count * (MAXABBREVLEN + strlen(delim())) + 1];
    Key::keyToUserString(refkey, varlist, keystr, delim());

    const char* pre = !htmlMode ? "" : (blue ? "<tr class=r1>" : "<tr>");
    const char* fmt = format(printLift, rel == NULL || printCalc);
    double lift = value / iviValue;

    if (rel == NULL || printCalc) {
        double res = value - refvalue;
        if (printLift) {

            fprintf(fd, fmt, pre, keystr, refvalue, refvalue * sample_size - adjustConstant, value, value * sample_size - adjustConstant, res, iviValue, iviValue * sample_size - adjustConstant, lift);
        } else {

            fprintf(fd, fmt, pre, keystr, refvalue, refvalue * sample_size - adjustConstant, value, value * sample_size - adjustConstant, res);
        }

    } else if(rel != NULL) { 
        if (printLift) {
            fprintf(fd, fmt, pre, keystr, refvalue, refvalue * sample_size - adjustConstant, iviValue, iviValue * sample_size - adjustConstant, lift); 

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

    double value_total = 0.0;
    double refValue_total = 0.0;
    double iviValue_total = 0.0;

    KeySegment* lastRefKey = NULL;

    bool sawUndefinedLift = false;

    auto tableAction = [&](Relation* rel, double value, KeySegment* refkey, double refvalue, double iviValue) {

        if (iviValue == 0 && value == 0) {
            sawUndefinedLift = true;   
        }

        value_total += value;
        refValue_total += refvalue;
        iviValue_total += iviValue;
        printTableRow(fd, blue, varlist, var_count, rel, value, refkey, refvalue, iviValue, adjustConstant, sample_size, printLift, printCalc);
        blue = !blue;
        lastRefKey = refkey;
    };


    tableIteration(input_table, varlist, rel, fit_table, indep_table, var_count, tableAction);


    auto tableTotals = 
        [this,fd,adjustConstant,rel,printLift,printCalc,var_count,lastRefKey,varlist]
        (double value, double refvalue, double ivivalue, double sample_size) {

        const char* pre = !htmlMode ? "" : "<tr>";
        const char* fmt = format(printLift, rel == NULL || printCalc);

        double lift = value / ivivalue; 

        char* keystr = new char[var_count * (MAXABBREVLEN + strlen(delim())) + 1];
        Key::keyToUserString(lastRefKey, varlist, keystr, delim(), false);

        if (printCalc) {
            double res = value - refvalue;
            if (printLift) {

                fprintf(fd, fmt, pre, keystr, refvalue, refvalue * sample_size - adjustConstant, value, value * sample_size - adjustConstant, res, ivivalue, ivivalue * sample_size - adjustConstant, lift);
            } else {
                fprintf(fd, fmt, pre, keystr, refvalue, refvalue * sample_size - adjustConstant, value, value * sample_size - adjustConstant, res);
            }

        } else if(rel != NULL) { 
            if (printLift) {
                fprintf(fd, fmt, pre, keystr, refvalue, refvalue * sample_size - adjustConstant, ivivalue, ivivalue * sample_size - adjustConstant, lift); 

            } else {
                fprintf(fd, fmt, pre, keystr, refvalue, refvalue * sample_size - adjustConstant); 
            }
        }
    };


    tableTotals(value_total, refValue_total, iviValue_total, sample_size);

    header(fd, rel, printLift, printCalc, false);
    
    footer(fd);

    if ((printCalc && (1 - value_total) > PRINT_MIN)
        || (printLift && (1 - iviValue_total > PRINT_MIN))
        || sawUndefinedLift) {
        printf("Note: ");
    }
    if (printCalc && (1 - value_total) > PRINT_MIN) {
        printf("The calculated probabilities sum to less than 1 (and the total residual is less than 0), possibly because the calculated distribution has probability distributed over states that were not observed in the data. \n");
    }
    if (printLift && (1 - iviValue_total > PRINT_MIN)) {
        printf("The independence probabilities sum to less than 1, possibly because the independence distribution has probability distributed over states that were not observed in the data. \n");
    }
    if (sawUndefinedLift) {
        printf("One or more states has an undefined (\"-nan\") lift value, because the calculated and independence probabilities are both 0, possibly because the state was never seen in the training data. \n");
    }
    if ((printCalc && (1 - value_total) > PRINT_MIN)
        || (printLift && (1 - iviValue_total > PRINT_MIN))
        || sawUndefinedLift) {
        newl(fd);
        newl(fd);
    }
}
