// tests/example_test.cpp
#include <gtest/gtest.h>
#include "../include/Input.h"  // Include the header file of the code you want to test

// Test case
TEST(ExampleTest, TestCase1) {
    // Test logic here
    EXPECT_EQ(2, 1 + 1);
}

// Add more test cases as needed

int main(int argc, char** argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
