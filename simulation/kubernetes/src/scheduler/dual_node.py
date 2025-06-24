import cvxpy as cp
import numpy as np

class centralized_solver()

  #The stopping condition for the algorithm (e.g., subsequent iterations varying below a set tolerance)
  def stopcondition()
    return true


  #The dual descent algorithm
  def dual_descent(x,G,constraints,objective)
    #initialize lambda to all 0s
    lambda = np.zeros(len(G),1)
    #Set the stepsize alpha (tunable parameter)
    alpha = 1
    #until we hit the stopping condition, repeat
    while self.stopcondition()
      #Step 1: Primal Update
      #create the new problem with updated lambda & solve it
      currentobj = cp.Maximize(objective + (lambda.transpose @ G @ x))
      currentprob = cp.Problem(currentobj,constraints)
      currentprob.solve()

      #Step 2: Sharing Step
      # ignored since this is a centralized implementation

      #Step 3: Dual Update
      lambda = lambda - alpha * G @ x.value

    #once we're done, return the solved-for values of x
    return x.value
