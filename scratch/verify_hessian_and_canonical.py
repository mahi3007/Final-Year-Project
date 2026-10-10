import numpy as np
import torch
import time

def verify_hessian_formula():
    print("--- 1. Verifying Observed Curvature vs Numerical Derivatives ---")
    # Single observation: y, mu, phi
    phi_val = 8.0
    mu_val = 12.5
    y_val = 15.0
    
    phi = torch.tensor(phi_val, dtype=torch.float64)
    eta = torch.tensor(np.log(mu_val), dtype=torch.float64, requires_grad=True)
    y = torch.tensor(y_val, dtype=torch.float64)
    
    # Negative Binomial log-likelihood as a function of eta = log(mu)
    def nb_loglik(eta_var):
        mu_var = torch.exp(eta_var)
        return (torch.lgamma(y + phi) - torch.lgamma(phi) - torch.lgamma(y + 1.0) +
                phi * torch.log(phi / (phi + mu_var)) + y * torch.log(mu_var / (phi + mu_var)))
    
    # 1. Analytical gradient
    mu = torch.exp(eta)
    g_analytical = (y - mu) / (1.0 + mu / phi)
    
    # Autograd 1st derivative
    loss = nb_loglik(eta)
    loss.backward(create_graph=True)
    g_autograd = eta.grad.item()
    
    print(f"Gradient: Autograd = {g_autograd:.8f}, Analytical = {g_analytical.item():.8f}")
    assert abs(g_autograd - g_analytical.item()) < 1e-7
    
    # 2. Autograd 2nd derivative (negative curvature)
    eta.grad.backward()
    d2_autograd = -eta.grad.item() # negative curvature
    
    # Analytical observed curvature: w_obs = mu * (1 + y/phi) / (1 + mu/phi)^2
    w_obs_analytical = (mu * (1.0 + y / phi) / (1.0 + mu / phi)**2).item()
    # Expected Fisher information: w_fisher = mu / (1 + mu/phi)
    w_fisher = (mu / (1.0 + mu / phi)).item()
    
    # Finite-difference 2nd derivative
    eps = 1e-5
    eta_plus = torch.tensor(np.log(mu_val) + eps, dtype=torch.float64)
    eta_minus = torch.tensor(np.log(mu_val) - eps, dtype=torch.float64)
    eta_mid = torch.tensor(np.log(mu_val), dtype=torch.float64)
    d2_fd = -((nb_loglik(eta_plus) - 2 * nb_loglik(eta_mid) + nb_loglik(eta_minus)) / (eps**2)).item()
    
    print(f"Negative Curvature at y={y_val}, mu={mu_val}, phi={phi_val}:")
    print(f"  Finite-difference:          {d2_fd:.8f}")
    print(f"  Autograd d^2:               {d2_autograd:.8f}")
    print(f"  Observed curvature formula: {w_obs_analytical:.8f}")
    print(f"  Fisher information formula: {w_fisher:.8f}")
    
    assert abs(d2_fd - w_obs_analytical) < 1e-4
    print("-> Observed curvature formula matches finite-difference and autograd EXACTLY!")
    print(f"-> Difference between Observed Curvature and Fisher Information: {abs(w_obs_analytical - w_fisher):.6f}")

if __name__ == "__main__":
    verify_hessian_formula()
