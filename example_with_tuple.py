import numpy as np
import problemgenerator.array as array
import problemgenerator.filter as filter
import problemgenerator.series as series

# Assume our data is a tuple of the form (x, y) where
# x has shape (100, 10) and y has shape (100,).
x = np.random.rand(100, 10)
y = np.random.rand(100,)
data = (x, y)

# Build a data model tree.
x_node = array.Array(10)
y_node = array.Array(1)
root = series.TupleSeries([x_node, y_node])

# Suppose we want to introduce NaN values (i.e. missing data)
# to y only (thus keeping x intact).
probability = .2
y_node.addfilter(filter.Missing(probability=probability))

# Feed the data to the root node.
output = root.process(data)

print("Output type (should be tuple):", type(output))
print("Output length (should be 2):", len(output))
print("Shape of first member of output tuple (should be (100, 10)):",
  output[0].shape)
print("Shape of second first member of output tuple (should be (100,)):",
  output[1].shape)
print("Number of NaNs in x (should be 0):",
  np.isnan(output[0]).sum())
print(f"Number of NaNs in y (should be close to {probability * y.size}):",
  np.isnan(output[1]).sum())