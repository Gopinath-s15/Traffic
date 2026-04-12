import matplotlib.pyplot as plt

plt.plot([1,2,3],[70,80,90])
plt.title("Accuracy Improvement")
# Save the plot since running it with plt.show() will block in a headless environment
plt.savefig('accuracy_graph.png')
print("Graph saved as accuracy_graph.png")
