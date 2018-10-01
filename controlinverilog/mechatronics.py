import numpy as np
from scipy import linalg
from scipy import signal
from .state_space import StateSpace


def _hamiltonian_matrix_continuous(g, sys):
    
    A, B, C, D = sys.params
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


def _matrices_discrete(g, sys):
    
    A, B, C, D = sys.params
    R = D.T @ D - g * g * np.identity(sys.n_input)
    Rinv = linalg.inv(R)
    m11 = np.identity(sys.n_order)
    m12 = np.zeros((sys.n_order, sys.n_order))
    m21 = C.T @ (np.identity(sys.n_input) - D @ Rinv @ D.T) @ C
    m22 = -(A + B @ Rinv @ D.T @ C).T
    m_mat = np.vstack((np.hstack((m11, m12)), np.hstack((m21, m22))))
    l11 = A + B @ Rinv @ D.T @ C
    l12 = B @ Rinv @ B.T
    l21 = np.zeros((sys.n_order, sys.n_order))
    l22 = np.identity(sys.n_order)
    l_mat = np.vstack((np.hstack((l11, l12)), np.hstack((l21, l22))))
    return m_mat, l_mat

    
def _initial_glb(sys):
    
    A, B, C, D = sys.params
    poles, _ = linalg.eig(A)
    pabs = np.abs(poles)
    
    if all(np.isreal(poles)) == True:
        wp = min(pabs)
    else:
        weight = np.abs(np.imag(poles) / (np.real(poles) * poles)) 
        wp, _ = max(zip(pabs, weight), key=lambda x: x[1])
    
    G0 = sys.transfer_function(0)
    Gwp = sys.transfer_function(1j*wp)
    
    sig = []
    for tf in (G0, Gwp, D):
        _, s, _ = linalg.svd(tf)
        sig.append(max(s))
    
    glb = max(sig)
    return glb


def _initial_glb_discrete(sys):
    
    poles = sys.poles()
    phip = np.angle(poles[np.argmax(np.abs(poles))])
    phis = np.array([0.0, phip, np.pi])
    
    def max_sv(phi):
        tf = sys.transfer_function(np.exp(1j*phi))
        _, sv, _ = linalg.svd(tf)
        return max(sv)
    
    vfunc = np.vectorize(max_sv)
    glb = max(vfunc(phis))
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


def _robust_no_unit(x_vals):
    """
    Parameters
    ----------
    x_vals : ndarray
        The array of values to test if they are on the unit circle.
    """
    x_phis = np.angle(x_vals)
    is_unit = np.isclose(np.exp(1j*x_phis), x_vals, rtol=1e-12, atol=1e-8)
    only_unit = x_phis[is_unit]
    no_unit = only_unit.shape[0] == 0
    return no_unit, np.sort(only_unit)


def _find_new_lower_bound(wi, sys):
    
    si = []
    for i in range(len(wi)-1):
        mi = 0.5 * (wi[i] + wi[i+1])
        Gw = sys.transfer_function(1j*mi)
        _, s, _ = linalg.svd(Gw)
        si.append(max(s))            
    glb = max(si)
    return glb


def _find_new_lower_bound_discrete(phis, sys):
    
    def max_sv(mi):
        Gw = sys.transfer_function(np.exp(1j*mi))
        _, sv, _ = linalg.svd(Gw)
        return max(sv)
        
    mis = np.diff(phis)
    vfunc = np.vectorize(max_sv)
    svs = vfunc(mis)
    glb = max(svs)
    return glb


def norm_hinf_continuous(sys):
    """
    Reference:    
    A fast algorithm to compute the H$\infty$-norm of a transfer function 
    matrix, N.A. Bruinsma and M. Steinbuch, Systems \&amp; Control Letters,
    1990, 14(4) pp. 287 - 293, 10.1016/0167-6911(90)90049-Z
    """
    glb, gub = _initial_glb(sys), 0
    no_imaginary = False
    eps = 1e-8
    
    while no_imaginary == False:
        g = (1 + 2 * eps) * glb
        Hg = _hamiltonian_matrix_continuous(g, sys)
        e, _ = linalg.eig(Hg)
        no_imaginary, wi = _robust_no_imaginary(e)
        if no_imaginary == True:
            gub = g
        else:
            glb = _find_new_lower_bound(wi, sys)
            
    norm = 0.5 * (glb + gub)
    return norm


def norm_hinf_discrete(sys):
    """
    Reference:
    L∞-norm calculation for generalized state space systems in continuous and 
    discrete time, P. M. M. Bongers and O. H. Bosgra and M. Steinbuch,
    1991 American Control Conference, 10.23919/ACC.1991.4791655
    
    Parameters
    ----------
    sys : controlinverilog.StateSpace
    
    Returns
    -------
    norm : float
        H∞ norm of the system.
    """
    glb, gub, no_unit, eps = _initial_glb_discrete(sys), 0, False, 1e-8

    while no_unit == False:
        g = (1 + 2 * eps) * glb
        m_mat, l_mat = _matrices_discrete(g, sys)
        e, _ = linalg.eig(m_mat, l_mat)
        no_unit, phis = _robust_no_unit(e)
        if no_unit == True:
            gub = g
        else:
            glb = _find_new_lower_bound_discrete(phis, sys)
            
    norm = 0.5 * (glb + gub)
    return norm


def norm_h2_continuous(sys):
    """
    Numerically computes the H2 norm of a LTI continuous time system.
    
    Parameters
    ----------
    sys : controlinverilog.StateSpace
        The state space matrices (A, B, C, D).
        
    Returns
    -------
    norm : float
        The H$_2$ norm.
    """
    A, B, C, D = sys.params
    W0 = observability_gramian_continuous(A, C)
    norm = np.sqrt(np.trace(B.T @ W0 @ B))
    return norm


def norm_h2_discrete(sys):
    """
    Numerically computes the H$_2$ norm of a LTI discrete time system using 
    the shift operator.
    
    Parameters
    ----------
    sys : tuple of ndarray
        The state space matrices (A, B, C, D).
        
    Returns
    -------
    norm : float
        The H$_2$ norm.
    """
    A, B, C, D = sys.params
    if sys.delta is not None:
        A, B = (np.identity(sys.n_order) + sys.delta * A), sys.delta * B 
    W0 = observability_gramian_discrete(A, C)
    norm = np.sqrt(np.trace(B.T @ W0 @ B))
    return norm


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
    Q = -B @ B.T
    Wc = linalg.solve_continuous_lyapunov(A, Q)
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
    Q = B @ B.T
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
    Q = -C.T @ C
    Wo = linalg.solve_continuous_lyapunov(A.T, Q)
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
    Q = C.T @ C
    Wo = linalg.solve_discrete_lyapunov(A.T, Q)
    return Wo


def balanced_realization_discrete(sys):
    
    if not sys.is_shift():
        msg = 'Balanced realization for shift operator only.'
        raise ValueError(msg)
    
    A, B, C, D = sys.params
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
    return StateSpace(Ab, Bb, Cb, Db, dt=sys.dt)



def time_constant(sys, dt):
    """
    Returns
    -------
    tc : float
        The time constant of the slowest pole in the system.
    """
    A = sys[0]
    zeig = linalg.eigvals(A)
    zeig = zeig[np.nonzero(zeig)]
    seig = np.log(zeig)/dt
    r = min(abs(np.real(seig)))
    if r == 0.0:
        raise ValueError('The system needs to be asymtotically stable.')
    tc = 1.0 / r
    return tc


def step_response(sys, dt):
    
    A, B, C, D = sys
    tc = time_constant(sys, dt)
    n = round(7 * tc / dt)
    t, y = signal.dstep((A, B, C, D, dt), n=n)
    return t, np.squeeze(y)


def impulse_response(sys, n_tc=7):
    
    A, B, C, D = sys.coeffs
    if sys.delta is not None:
        A, B = (np.identity(sys.n_order) + sys.delta * A), sys.delta * B 
    ev, _ = linalg.eig(A)
    tc = time_constant(sys, sys.dt)
    n = round(n_tc * tc / sys.dt)
    t, y = signal.dstep((A, B, C, D, sys.dt), n=n)
    return t, np.squeeze(y)


def overshoot(sys, dt):
    """
    Returns
    -------
    The overshoot due to a unit step of the system.
    """
    _, y = step_response(sys, dt)
    return np.amax(np.squeeze(y))


def safe_gain(sys, dt):
    """
    
    gain = sum(|f[k]|)
    
    where f[k] is the impulse response of the system. To evaluate the impulse
    response, the system is simulated for 20x the time constant of the slowest
    pole of the system.
    """
    A, B, C, D = sys
    tc = time_constant(sys, dt)
    n = round(20 * tc / dt)
    _, y = signal.dimpulse((A, B, C, D, dt), n=n)
    gain = np.sum(np.abs(y))
    return gain


def metric_h2(sys, sys_q):
    
    sys_diff = sys - sys_q
    return norm_h2_discrete(sys_diff) / norm_h2_discrete(sys)


def metric_hinf(sys, sys_q):
    
    sys_diff = sys - sys_q
    return norm_hinf_discrete(sys_diff) / norm_hinf_discrete(sys)


def metric_pole(sys, sys_q):
    """Calculates the maximum difference between the poles of the system and 
    its quantized version.
    """
    poles = sys.poles()
    poles_q = sys_q.poles()
    metric = 0
    for ii in range(sys.n_order):
        diff_vec = np.abs(poles[ii] - poles_q) / np.abs(poles[ii])
        idx = np.argmin(diff_vec)
        if metric < diff_vec[idx]:
            metric = diff_vec[idx]
        poles_q = np.delete(poles_q, idx)
    return metric
    

def metric_impulse(sys, sys_q):
    """The size of the impulse is measured using the l2 norm. This metric only
    considers SISO systems.
    """        
    if not sys.is_siso():
        message = 'cof_scaling_method `impulse` only for SISO systems.'
        raise ValueError(message)
    sys_diff = sys - sys_q
    _, y = impulse_response(sys, n_tc=20.0)
    _, yd = impulse_response(sys_diff, n_tc=20.0)
    y, yd = y[0], yd[0]
    return np.sqrt(np.sum(yd * yd) / np.sum(y * y))

