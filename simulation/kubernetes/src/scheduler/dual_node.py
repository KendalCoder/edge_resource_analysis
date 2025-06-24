import cvxpy as cp
import numpy as np

class node()

  def __init__(self,constraints,x,objective,G,id)
    self.constraints = constraints
    self.x = x
    self.objective = objective
    self.G = G
    self.id = id


  #The stopping condition for the algorithm (e.g., subsequent iterations varying below a set tolerance)
  #This has to look at a global perspective, and so requires communication for whether everyone is done or not
  def stopcondition()
    return true


  #The sharing function that handles how nodes share x values with each other.
  #This takes as input this node's updated x value(s), and returns the full x vector
  #relevant to this node, including its own x value(s)
  def share(my_x)
    return 1

  #The dual descent algorithm
  def dual_descent()
    #initialize lambda to all 0s
    lambda = np.zeros(len(self.G),1)
    #Set the stepsize alpha (tunable parameter)
    alpha = 1
    #Define indexing that lets us grab either all x_i or all other x except x_i
    #This is left unspecified since the ordering for x & G may change. However,
    #I would recommend using the ordering presented in the CDC paper, since it
    #works with how I've defined the updates for currentobj and lambda.
    x_i = []
    x_ibar = []
    #initialize this node's current understanding of all other relevant nodes' x
    #This is needed to perform the primal and dual updates properly.
    currentx = zeros(G.shape[1],1)

    while self.stopcondition()
      #Step 1: Primal Update
      #Create the current objective with current lambda
      currentobj = cp.Maximize(self.objective + (lambda.transpose @ G @ x))
      #Fix all x other than this node's own copies
      constraints = [constraints, x[x_ibar] == currentx[x_ibar]]
      #solve
      currentprob = cp.Problem(currentobj,constraints)
      currentprob.solve()

      #Step 2: Sharing Step
      currentx = self.share(x.value)

      #Step 3: Dual Update
      lambda = lambda - alpha * G @ currentx

    #once complete, return this node's own decision (but not others)
    return x.value
