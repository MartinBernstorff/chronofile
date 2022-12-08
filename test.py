import matplotlib.pyplot as plt
import numpy as np

# Generate some data
np.random.seed(42)
data = np.random.normal(size=100)

# Create the figure and axes objects
fig, ax = plt.subplots()

# Plot the data as a dot plot
ax.scatter(np.zeros_like(data), data, marker="_", c="#2D2F31")

# Overlay a half-violin plot on top of the dot plot
ax.violinplot(
    data, vert=False, widths=0.5, showmeans=True, showextrema=True, showmedians=False
)

# Set the x-axis limits to show only the left half of the plot
ax.set_xlim(-0.5, 0.5)

# Show the plot
plt.show()

pass
