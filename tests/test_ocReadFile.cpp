#include <gtest/gtest.h>
#include <fstream>
#include "../include/Input.h" // Include the necessary headers for ocReadFile and other dependencies
#include "../include/Options.h"
#include "../include/VariableList.h"

// Fixture class for setting up common data and state
class OcReadFileTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Set up any state or data needed for the tests
    }

    void TearDown() override {
        // Clean up any state or data after tests
    }
};
/*
// Function to count the number of lines in a file
int countLines(const char* filename) {
    std::ifstream file(filename);
    int lines = 0;
    std::string line;
    while (std::getline(file, line)) {
        ++lines;
    }
    return lines;
}
*/
// Function to count the number of lines in a file that begin with a space
int countLines(const char* filename) {
    std::ifstream file(filename);
    int lines = 0;
    std::string line;
    while (std::getline(file, line)) {
        if (!line.empty() && line[0] == ' ') {
            ++lines;
        }
    }
    return lines;
}

// Test case for ocReadFile
TEST_F(OcReadFileTest, ReadFile) {
    // Open the file
    FILE *file = fopen("./tests/data/readFile.txt", "r");
    ASSERT_NE(file, nullptr) << "Failed to open file";

    // Prepare the arguments for ocReadFile
    Options options;
    Table *indata = nullptr;
    Table *testdata = nullptr;
    VariableList *vars = nullptr;

    // Call the function
    int result = ocReadFile(file, &options, &indata, &testdata, &vars);

    // Close the file
    fclose(file);

    // Count the number of lines in the test file
    int expected_lines = countLines("./tests/data/readFile.txt");

    // Check the result
    EXPECT_EQ(result, expected_lines) << "ocReadFile returned the wrong number of lines";

    // Additional checks can be added here to validate the contents of indata, testdata, and vars
    // For example:
    // EXPECT_EQ(indata->some_property, expected_value);
    // EXPECT_EQ(testdata->some_property, expected_value);
    // EXPECT_EQ(vars->some_property, expected_value);

    // Clean up dynamically allocated data if necessary
    delete indata;
    delete testdata;
    delete vars;
}

// Main function to run the tests
int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

