import numpy as np

n= 5

T = np.vstack([
    np.hstack([np.eye(n-1), -np.ones((n-1, 1))]),  # Upper block
    np.hstack([np.zeros((1, n-1)), np.ones((1, 1))])  # Lower block
])

print(T)