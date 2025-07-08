from scheduler import Scheduler  
import cvxpy as cp
import numpy as np


class DualDescent(Scheduler):

    def __init__(self, constraints, x, objective, G, node_id, tolerance=1e-3, max_iters=100):
        """
        Initialize the Dual Descent scheduler.
        Args:
            constraints (list): List of cvxpy constraints for this node.
            x (cvxpy.Variable): Decision variable(s) for this node.
            objective (cvxpy.Expression): Objective function for this node.
            G (np.ndarray): Coupling matrix between nodes.
            node_id (int): Identifier/index of this node.
            tolerance (float): Convergence tolerance.
            max_iters (int): Maximum number of iterations.
        """

        self.constraints = constraints
        self.x = x
        self.objective = objective
        self.G = G
        self.node_id = node_id
        self.lambda_vec = np.zeros((G.shape[0], 1))
        self.alpha = 1  # Step size (can be tuned)
        self.current_x = np.zeros((G.shape[1], 1))  # Estimates of all nodes' variables
        self.tolerance = tolerance
        self.max_iters = max_iters

    def stopcondition(self, prev_x, iters):
        #Define stopping condition for the dual descent algorithm.        # Returns: bool: True if stopping condition is met, False otherwise.
        # This could be based on convergence criteria, maximum iterations, or tolerance level.
        # TODO: Implement convergence check based on tolerance or max iterations
        if prev_x is not None and self.x.value is not None:
            if np.linalg.norm(self.x.value - prev_x) < self.tolerance:
                return True
        if iters >= self.max_iters:
            return True
        return False

    def share(self, my_x):

        #Share updated decision variables with other nodes. my_x (np.ndarray): This node's updated decision variables. 
        # Returns:np.ndarray: Updated global decision vector including this node's value.

        # TODO: Implement communication logic with other nodes

        # For now, just returns my_x as placeholder

        return my_x

    def schedule(self):
        #Run the dual descent algorithm until stopping condition is met. This method performs primal and dual updates iteratively.
        # Returns: np.ndarray: This node's optimized decision variables.
        iters = 0
        prev_x = None
        while not self.stopcondition(prev_x, iters):

            # Step 1: Primal update
            current_obj = cp.Maximize(self.objective + self.lambda_vec.T @ self.G @ self.x)

            # Fix x variables for other nodes to current estimates

            primal_constraints = self.constraints + [
                self.x[i] == self.current_x[i] for i in range(self.G.shape[1]) if i != self.node_id
            ]
            prob = cp.Problem(current_obj, primal_constraints)
            prob.solve()

            # Step 2: Share updated x with other nodes
            self.current_x = self.share(self.x.value)

            # Step 3: Dual update
            self.lambda_vec = self.lambda_vec - self.alpha * self.G @ self.current_x
            iters += 1
            prev_x = self.x.value.copy() if self.x.value is not None else None
        # Return this node's decision variable value
        return self.x.value

