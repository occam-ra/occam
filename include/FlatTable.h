#ifndef ___FlatTable
#define ___FlatTable

#include <stdlib.h>
#include <stdio.h>
#include <utility>

#define get(i) if (i < size_) { return data[i]; } else { out_of_bounds(); }
struct flat_table {
    private:
        long long size_;
        double* data = nullptr;
        void reset() { size_ = 0; data = nullptr; }
    public:
    long long size() const { return size_; }
    flat_table(long long size) : size_{size}, data{new double[size]} {}
    ~flat_table() { delete[] data; }

    flat_table(flat_table&& other) : data {other.data}, size_{other.size_} { other.reset(); }
    flat_table& operator=(flat_table&& other) { data = other.data; size_ = other.size_; other.reset(); }

    double& operator[](long long i) { get(i); }
    const double& operator[](long long i) const { get(i); }

    flat_table(flat_table const&) = delete;
    flat_table& operator=(flat_table const&) = delete;
 
 
    void dump() const {
        for (long long i = 0; i < size_;  ++i) { printf("%g", data[i]); }
    }
 
    private: 
    void out_of_bounds() const { 
        printf("Error: Array out of bounds exception in 'flat_table'.\n"
                "This is a low-level program error - please report to"
                " h.forrest.alexander@gmail.com for assistance.");
        exit(1);
    }
};
#undef get
#endif
