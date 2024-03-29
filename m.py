from abc import ABC, abstractmethod
import numpy as np

""" 
Base class for sharing 
attributes and functions of FD 
"""
class FiniteDifferences(object):

    def __init__(
        self, S0, K, r=0.05, T=1, 
        sigma=0, Smax=1, M=1, N=1, is_put=False
    ):
        self.S0 = S0
        self.K = K
        self.r = r
        self.T = T
        self.sigma = sigma
        self.Smax = Smax
        self.M, self.N = M, N
        self.is_call = not is_put

        self.i_values = np.arange(self.M)
        self.j_values = np.arange(self.N)
        self.grid = np.zeros(shape=(self.M+1, self.N+1))
        self.boundary_conds = np.linspace(0, Smax, self.M+1)

    @property
    def dS(self):
        return self.Smax/float(self.M)

    @property
    def dt(self):
        return self.T/float(self.N)

    @abstractmethod
    def setup_boundary_conditions(self):
        raise NotImplementedError('Implementation required!')

    @abstractmethod
    def setup_coefficients(self):
        raise NotImplementedError('Implementation required!')

    @abstractmethod
    def traverse_grid(self):
        """  
        Iterate the grid backwards in time 
        """
        raise NotImplementedError('Implementation required!')

    @abstractmethod
    def interpolate(self):
        """
        Use piecewise linear interpolation on the initial
        grid column to get the closest price at S0.
        """
        return np.interp(
            self.S0, self.boundary_conds, self.grid[:,0])

    def price(self):
        self.setup_boundary_conditions()
        self.setup_coefficients()
        self.traverse_grid()
        return self.interpolate()
    
import numpy as np

""" 
Explicit method of Finite Differences 
"""
class FDExplicitEu(FiniteDifferences):

    def setup_boundary_conditions(self):
        if self.is_call:
            self.grid[:,-1] = np.maximum(
                0, self.boundary_conds - self.K)
            self.grid[-1,:-1] = (self.Smax-self.K) * \
                np.exp(-self.r*self.dt*(self.N-self.j_values))
        else:
            self.grid[:,-1] = np.maximum(
                0, self.K-self.boundary_conds)
            self.grid[0,:-1] = (self.K-self.Smax) * \
                np.exp(-self.r*self.dt*(self.N-self.j_values))

    def setup_coefficients(self):
        self.a = 0.5*self.dt*((self.sigma**2) *
                              (self.i_values**2) -
                              self.r*self.i_values)
        self.b = 1 - self.dt*((self.sigma**2) *
                              (self.i_values**2) +
                              self.r)
        self.c = 0.5*self.dt*((self.sigma**2) *
                              (self.i_values**2) +
                              self.r*self.i_values)

    def traverse_grid(self):
        for j in reversed(self.j_values):
            for i in range(self.M)[2:]:
                self.grid[i,j] = \
                    self.a[i]*self.grid[i-1,j+1] +\
                    self.b[i]*self.grid[i,j+1] + \
                    self.c[i]*self.grid[i+1,j+1]


import numpy as np
import scipy.linalg as linalg

""" 
Explicit method of Finite Differences 
"""
class FDImplicitEu(FDExplicitEu):

    def setup_coefficients(self):
        self.a = 0.5*(self.r*self.dt*self.i_values -
                      (self.sigma**2)*self.dt*\
                          (self.i_values**2))
        self.b = 1 + \
                 (self.sigma**2)*self.dt*\
                    (self.i_values**2) + self.r*self.dt
        self.c = -0.5*(self.r*self.dt*self.i_values +
                       (self.sigma**2)*self.dt*\
                           (self.i_values**2))
        self.coeffs = np.diag(self.a[2:self.M],-1) + \
                      np.diag(self.b[1:self.M]) + \
                      np.diag(self.c[1:self.M-1],1)

    def traverse_grid(self):
        """ Solve using linear systems of equations """
        P, L, U = linalg.lu(self.coeffs)
        aux = np.zeros(self.M-1)

        for j in reversed(range(self.N)):
            aux[0] = np.dot(-self.a[1], self.grid[0, j])
            x1 = linalg.solve(L, self.grid[1:self.M, j+1]+aux)
            x2 = linalg.solve(U, x1)
            self.grid[1:self.M, j] = x2
            
import scipy.linalg as linalg

""" 
Crank-Nicolson method of Finite Differences 
"""
class FDCnEu(FDExplicitEu):

    def setup_coefficients(self):
        self.alpha = 0.25*self.dt*(
            (self.sigma**2)*(self.i_values**2) - \
            self.r*self.i_values)
        self.beta = -self.dt*0.5*(
            (self.sigma**2)*(self.i_values**2) + self.r)
        self.gamma = 0.25*self.dt*(
            (self.sigma**2)*(self.i_values**2) +
            self.r*self.i_values)
        self.M1 = -np.diag(self.alpha[2:self.M], -1) + \
                  np.diag(1-self.beta[1:self.M]) - \
                  np.diag(self.gamma[1:self.M-1], 1)
        self.M2 = np.diag(self.alpha[2:self.M], -1) + \
                  np.diag(1+self.beta[1:self.M]) + \
                  np.diag(self.gamma[1:self.M-1], 1)

    def traverse_grid(self):
        """ Solve using linear systems of equations """
        P, L, U = linalg.lu(self.M1)

        for j in reversed(range(self.N)):
            x1 = linalg.solve(
                L, np.dot(self.M2, self.grid[1:self.M, j+1]))
            x2 = linalg.solve(U, x1)
            self.grid[1:self.M, j] = x2
            
import numpy as np

"""
Price a down-and-out option by the Crank-Nicolson
method of finite differences.
"""
class FDCnDo(FDCnEu):

    def __init__(
        self, S0, K, r=0.05, T=1, sigma=0, 
        Sbarrier=0, Smax=1, M=1, N=1, is_put=False
    ):
        super(FDCnDo, self).__init__(
            S0, K, r=r, T=T, sigma=sigma,
            Smax=Smax, M=M, N=N, is_put=is_put
        )
        self.barrier = Sbarrier
        self.boundary_conds = \
            np.linspace(Sbarrier, Smax, M+1)
        self.i_values = self.boundary_conds/self.dS

    @property
    def dS(self):
        return (self.Smax-self.barrier)/float(self.M)
    
import numpy as np
import sys

""" 
Price an American option by the Crank-Nicolson method 
"""
class FDCnAm(FDCnEu):

    def __init__(self, S0, K, r=0.05, T=1, sigma=0, 
            Smax=1, M=1, N=1, omega=1, tol=0, is_put=False):
        super(FDCnAm, self).__init__(S0, K, r=r, T=T, 
            sigma=sigma, Smax=Smax, M=M, N=N, is_put=is_put)
        self.omega = omega
        self.tol = tol
        self.i_values = np.arange(self.M+1)
        self.j_values = np.arange(self.N+1)

    def setup_boundary_conditions(self):
        if self.is_call:
            self.payoffs = np.maximum(0, 
                self.boundary_conds[1:self.M]-self.K)
        else:
            self.payoffs = np.maximum(0, 
                self.K-self.boundary_conds[1:self.M])

        self.past_values = self.payoffs
        self.boundary_values = self.K * np.exp(
                -self.r*self.dt*(self.N-self.j_values))
        
    def calculate_payoff_start_boundary(self, rhs, old_values):
        payoff = old_values[0] + \
            self.omega/(1-self.beta[1]) * \
                (rhs[0] - \
                 (1-self.beta[1])*old_values[0] + \
                 self.gamma[1]*old_values[1])

        return max(self.payoffs[0], payoff)      
    
    def calculate_payoff_end_boundary(self, rhs, old_values, new_values):
        payoff = old_values[-1] + \
            self.omega/(1-self.beta[-2]) * \
                (rhs[-1] + \
                 self.alpha[-2]*new_values[-2] - \
                 (1-self.beta[-2])*old_values[-1])

        return max(self.payoffs[-1], payoff)
    
    def calculate_payoff(self, k, rhs, old_values, new_values):
        payoff = old_values[k] + \
            self.omega/(1-self.beta[k+1]) * \
                (rhs[k] + \
                 self.alpha[k+1]*new_values[k-1] - \
                 (1-self.beta[k+1])*old_values[k] + \
                 self.gamma[k+1]*old_values[k+1])

        return max(self.payoffs[k], payoff)

    def traverse_grid(self):
        """ Solve using linear systems of equations """
        aux = np.zeros(self.M-1)
        new_values = np.zeros(self.M-1)

        for j in reversed(range(self.N)):
            aux[0] = self.alpha[1]*(self.boundary_values[j] +
                                    self.boundary_values[j+1])
            rhs = np.dot(self.M2, self.past_values) + aux
            old_values = np.copy(self.past_values)
            error = sys.float_info.max

            while self.tol < error:
                new_values[0] = \
                    self.calculate_payoff_start_boundary(
                        rhs, old_values)            

                for k in range(self.M-2)[1:]:
                    new_values[k] = \
                        self.calculate_payoff(
                            k, rhs, old_values, new_values)                    

                new_values[-1] = \
                    self.calculate_payoff_end_boundary(
                        rhs, old_values, new_values)

                error = np.linalg.norm(new_values-old_values)
                old_values = np.copy(new_values)

                self.past_values = np.copy(new_values)

        self.values = np.concatenate(
            ([self.boundary_values[0]], new_values, [0]))

    def interpolate(self):
        # Use linear interpolation on final values as 1D array
        return np.interp(
            self.S0, self.boundary_conds, self.values)

option = FDCnAm(50, 50, r=0.1, T=5./12., 
    sigma=0.4, Smax=100, M=100, N=42, omega=1.2, tol=0.001)
print(option.price())

    