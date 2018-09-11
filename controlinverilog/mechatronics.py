# import control
import numpy as np
from scipy import linalg
from scipy import integrate
from scipy import signal


def _hamiltonian_matrix(g, sys):
    
    A, B, C, D = sys
    r, c = D.shape
    R = D.T.dot(D) - g * g * np.identity(c)
    S = D.dot(D.T) - g * g * np.identity(r)
    Rinv = linalg.inv(R)
    Sinv = linalg.inv(S)
    H11 = A - B.dot(Rinv).dot(D.T).dot(C)
    H12 = -g * B.dot(Rinv).dot(B.T)
    H21 = g * C.T.dot(Sinv).dot(C)
    H22 = -A.T + C.T.dot(D).dot(Rinv).dot(B.T)
    Hg = np.vstack((np.hstack((H11, H12)), np.hstack((H21, H22))))
    return Hg


def _tf(s, sys):
    
    A, B, C, D = sys
    n = A.shape[0]
    poles = linalg.inv(s * np.identity(n) - A)
    return C.dot(poles).dot(B) + D
    
    
def _initial_glb(sys):
    
    A, B, C, D = sys
    poles, _ = linalg.eig(A)
    pabs = np.abs(poles)
    
    if all(np.isreal(poles)) == True:
        wp = min(pabs)
    else:
        weight = np.abs(np.imag(poles) / (np.real(poles) * poles)) 
        wp, _ = max(zip(pabs, weight), key=lambda x: x[1])
    
    G0 = _tf(0, sys)
    Gwp = _tf(1j*wp, sys)
    
    sig = []
    for tf in (G0, Gwp, D):
        _, s, _ = linalg.svd(tf)
        sig.append(max(s))
    
    glb = max(sig)
    return glb


def _robust_no_imaginary(x_vals):
    """
    Returns
    -------
    no_imaginary : bool
        True if all values are not imaginary, otherwise False.
    only_imag : list of float
        Returns the imaginary components of the imaginary values. 
        The list is sorted.
    """
    x_imag = np.imag(x_vals)
    is_imag = np.isclose(1j*x_imag, x_vals, rtol=1e-12, atol=1e-8)
    only_imag = []
    for (is_, xi) in zip(is_imag, x_imag):
        if is_ == True:
            only_imag.append(xi)
    no_imaginary = len(only_imag) == 0
    return no_imaginary, sorted(only_imag)


def _find_new_lower_bound(wi, sys):
    
    si = []
    for i in range(len(wi)-1):
        mi = 0.5 * (wi[i] + wi[i+1])
        Gw = _tf(1j*mi, sys)
        _, s, _ = linalg.svd(Gw)
        si.append(max(s))            
    glb = max(si)
    return glb


def norm_hinf_continuous(sys):
    
    glb, gub = _initial_glb(sys), 0
    no_imaginary = False
    eps = 1e-8
    
    while no_imaginary == False:
        g = (1 + 2 * eps) * glb
        Hg = _hamiltonian_matrix(g, sys)
        e, _ = linalg.eig(Hg)
        no_imaginary, wi = _robust_no_imaginary(e)
        if no_imaginary == True:
            gub = g
        else:
            glb = _find_new_lower_bound(wi, sys)
            
    norm = 0.5 * (glb + gub)
    return norm


def norm_h2_discrete_siso(sys):
    """
    Numerically computes the H$_2$ norm of a SISO LTI discrete time system.
    
    Parameters
    ----------
    sys : tuple of ndarray
        The state space matrices (A, B, C, D).
        
    Returns
    -------
    norm : int
        The H$_2$ norm.
    """
    A, B, C, D = sys
    
    if B.shape[1] != 1 or C.shape[0] != 1:
        raise ValueError('This algorithm applies to SISO systems.')
    
    def integrand(w):
        z = np.exp(1j*w)
        tf = C @ linalg.inv(z*np.identity(A.shape[0]) - A) @ B + D
        return np.abs(tf) ** 2
        
    res =  integrate.quad(integrand, -np.pi, np.pi)
    return np.sqrt(1/(2*np.pi) * res[0])
    

def norm_hinf_discrete_siso(sys, samples=1000):
    """
    Numerically computes the H$_\infty$ norm of a SISO LTI discrete time 
    system.
    
    Parameters
    ----------
    sys : tuple of ndarray
        The state space matrices (A, B, C, D).
    samples : int
        The number of points in the frequency domain to evalute the transfer 
        function of the system.
        
    Returns
    -------
    norm : int
        The H$_\infty$ norm.
    """
    A, B, C, D = sys
    
    if B.shape[1] != 1 or C.shape[0] != 1:
        raise ValueError('This algorithm applies to SISO systems.')
    
    def magnitude(w):
        z = np.exp(1j*w)
        tf = C @ linalg.inv(z*np.identity(A.shape[0]) - A) @ B + D
        return np.abs(tf)
        
    vfunc = np.vectorize(magnitude)
    freq = np.linspace(0, np.pi, samples)
    return np.amax(vfunc(freq))


def norm_h2_discrete(sys):
    """
    Numerically computes the H$_2$ norm of a LTI discrete time system.
    
    Parameters
    ----------
    sys : tuple of ndarray
        The state space matrices (A, B, C, D).
        
    Returns
    -------
    norm : int
        The H$_2$ norm.
    """
    A, B, C, D = sys
    W0 = observability_gramian_discrete(A, C)
    norm = np.sqrt(np.trace(B.T @ W0 @ B))
    return norm


def order(sys):
    
    A = sys[0]
    order = A.shape[0]
    return order


def lqr(A, B, Q, R):
    """Solve the continuous time lqr controller.
    
    dx/dt = A x + B u
        
    cost = integral x.T*Q*x + u.T*R*u

    Parameters
    ----------
    A : ndarray
        The system state matrix.
    B : ndarray
        The system input matrix.
    Q : ndarray
        The weighting matrix for the states.
    R : ndarray
        The weighting matrix for the control action.
        
    Returns
    -------
    K : ndarray
        The state feedback matrix.
    P : ndarray
        The solution to the Algebraic Ricatti Equation.
    w : ndarray
        The eigenvalues of the closed loop system.
    """
    P = linalg.solve_continuous_are(A, B, Q, R)
    Rinv = linalg.inv(R)
    K = Rinv.dot(B.T).dot(P) 
    w, _ = linalg.eig(A - B.dot(K))
    return K, P, w


def controllability_gramian_continuous(A, B):
    """Calculates the controllabilty gramian of a continuous time LTI system.
    
    Parameters
    ----------
    A : ndarray
        The state matrix.
    B : ndarray
        The input matrix.
        
    Returns
    -------
    Wc : ndarray
        The controllability gramian.
    """
    Q = np.dot(-B, B.T)
    Wc = linalg.solve_lyapunov(A, Q)
    return Wc


def controllability_gramian_discrete(A, B):
    """Calculates the controllabilty gramian of a discrete time LTI system.
    
    Parameters
    ----------
    A : ndarray
        The state matrix.
    B : ndarray
        The input matrix.
        
    Returns
    -------
    Wc : ndarray
        The controllability gramian.
    """
    Q = np.dot(B, B.T)
    Wc = linalg.solve_discrete_lyapunov(A, Q)
    return Wc


def observability_gramian_continuous(A, C):
    """Calculates the observability gramian of a continuous time LTI system.
    
    Parameters
    ----------
    A : ndarray
        The state matrix.
    C : ndarray
        The output matrix.
        
    Returns
    -------
    Wo : ndarray
        The observability gramian.
    """
    Q = np.dot(-C.T, C)
    Wo = linalg.solve_lyapunov(A, Q)
    return Wo


def observability_gramian_discrete(A, C):
    """Calculates the observability gramian of a discrete time LTI system.
    
    Parameters
    ----------
    A : ndarray
        The state matrix.
    C : ndarray
        The output matrix.
        
    Returns
    -------
    Wc : ndarray
        The observability gramian.
    """
    Q = np.dot(C.T, C)
    Wo = linalg.solve_discrete_lyapunov(A.T, Q)
    return Wo


def balanced_realization_discrete(sys):
    """
    """
    A, B, C, D = sys
    P = controllability_gramian_discrete(A, B)
    Q = observability_gramian_discrete(A, C)
    R = linalg.cholesky(P, lower=True)
    RtranQR = R.T.dot(Q).dot(R)
    U, s, _ = linalg.svd(RtranQR)
    ssqrtsqrt = np.sqrt(np.sqrt(s))
    SigmaSqrtInv = np.diag(np.reciprocal(ssqrtsqrt))
    # SigmaSqrt = np.diag(np.sqrt(np.sqrt(s)))
    T = R.dot(U).dot(SigmaSqrtInv)
    Tinv = linalg.inv(T)
    # Tinv = SigmaSqrt.dot(U.T).dot(linalg.inv(R))
    Ab = Tinv.dot(A).dot(T)
    Bb = Tinv.dot(B)
    Cb = C.dot(T)
    Db = D
    return (Ab, Bb, Cb, Db)


def step_info(sys, dt):
    
    A, B, C, D = sys
    
    # Compute simulation time.
    zeig = linalg.eigvals(A)
    seig = np.log(zeig)/dt
    r = min(abs(np.real(seig)))
    if r == 0.0:
        r = 1.0
    tc = 1.0 / r
    t = np.linspace(0.0, 7 * tc, 1000)
    
    return signal.dstep((A, B, C, D, dt), t=t)
    