import cvxpy as cp
import numpy as np

class centralized_solver:
  # Initialize the solver with a tolerance and maximum iterations
  # tolerance: the threshold for stopping the algorithm
  # max_iters: the maximum number of iterations to run

  def __init__(self, tolerance=1e-3, max_iters=100):
    self.tolerance = tolerance
    self.max_iters = max_iters

# The stopping condition for the algorithm (e.g., subsequent iterations varying below a set tolerance)
def stopcondition(self, prev_x, current_x):
    if prev_x is None:
        return False
    return np.linalg.norm(prev_x - current_x) < self.tolerance

# The dual descent algorithm
def dual_descent(self, x, G, constraints, objective):
    # initialize lambda to all 0s
    lambda_vec = np.zeros((G.shape[0], 1))
    # Set the stepsize alpha (tunable parameter)
    alpha = 1
    prev_x = None

    # until we hit the stopping condition, repeat
    while not self.stopcondition(prev_x, x.value):
        # Step 1: Primal Update
        # create the new problem with updated lambda & solve it
        current_obj = cp.Maximize(objective + cp.matmul(lambda_vec.T, G @ x))
        prob = cp.Problem(current_obj, constraints)
        prob.solve()

        # Step 2: Sharing Step
        # ignored since this is a centralized implementation
        if x.value is None:
            raise RuntimeError("Solver failed to compute x")

        # Step 3: Dual Update
        lambda_vec = lambda_vec - alpha * (G @ x.value)

        # Step 3: Check Stopping Condition
        if self.stopcondition(prev_x, x.value):
            break
        prev_x = x.value.copy()

    # once we're done, return the solved-for values of x
    return x.value
