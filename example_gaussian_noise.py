import numpy as np
import problemgenerator.array as array
import problemgenerator.filter as filter
import problemgenerator.series as series
import matplotlib.pyplot as plt

x_file, y_file = "example_data/x.npy", "example_data/y.npy"
x = np.load(x_file)
y = np.load(y_file)
data = (x, y)

x_node = array.Array(x[0].shape)
x_node.addfilter(filter.GaussianNoise(0, .1))
y_node = array.Array(y[0].shape)
root_node = series.TupleSeries([x_node, y_node])

out_x, out_y = root_node.process(data)
print((y != out_y).sum(), "elements of y have been modified in (should be 0).")

fig, axs = plt.subplots(2, 4)
for i in range(4):
    img_ind = np.random.randint(len(x))
    axs[0, i].matshow(x[img_ind], cmap='gray_r')
    axs[1, i].matshow(out_x[img_ind], cmap='gray_r')

plt.show()
