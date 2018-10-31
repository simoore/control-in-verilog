import numpy as np
from scipy import linalg


# from scipy import signal
# from .state_space import StateSpace

def _eval_tf(a, b, c, d, p):
    return c @ linalg.inv(p * np.identity(a.shape[0]) - a) @ b + d


def _hamiltonian_matrix_continuous(g, mat_a, mat_b, mat_c, mat_d):
    # A, B, C, D = sys.params
    r, c = mat_d.shape
    mat_r = mat_d.T.dot(mat_d) - g * g * np.identity(c)
    mat_s = mat_d.dot(mat_d.T) - g * g * np.identity(r)
    mat_r_inv = linalg.inv(mat_r)
    mat_s_inv = linalg.inv(mat_s)
    h11 = mat_a - mat_b.dot(mat_r_inv).dot(mat_d.T).dot(mat_c)
    h12 = -g * mat_b.dot(mat_r_inv).dot(mat_b.T)
    h21 = g * mat_c.T.dot(mat_s_inv).dot(mat_c)
    h22 = -mat_a.T + mat_c.T.dot(mat_d).dot(mat_r_inv).dot(mat_b.T)
    mat_hg = np.vstack((np.hstack((h11, h12)), np.hstack((h21, h22))))
    return mat_hg


def _matrices_discrete(g, mat_a, mat_b, mat_c, mat_d):
    # A, B, C, D = sys.params
    n_order, n_input = mat_b.shape
    mat_r = mat_d.T @ mat_d - g * g * np.identity(n_input)
    mat_r_inv = linalg.inv(mat_r)
    m11 = np.identity(n_order)
    m12 = np.zeros((n_order, n_order))
    m21 = mat_c.T @ (np.identity(n_input) - mat_d @ mat_r_inv @ mat_d.T) @ mat_c
    m22 = -(mat_a + mat_b @ mat_r_inv @ mat_d.T @ mat_c).T
    m_mat = np.vstack((np.hstack((m11, m12)), np.hstack((m21, m22))))
    l11 = mat_a + mat_b @ mat_r_inv @ mat_d.T @ mat_c
    l12 = mat_b @ mat_r_inv @ mat_b.T
    l21 = np.zeros((n_order, n_order))
    l22 = np.identity(n_order)
    l_mat = np.vstack((np.hstack((l11, l12)), np.hstack((l21, l22))))
    return m_mat, l_mat


def _initial_glb(mat_a, mat_b, mat_c, mat_d):
    # A, B, C, D = sys.params
    poles, _ = linalg.eig(mat_a)
    pabs = np.abs(poles)

    if all(np.isreal(poles)):
        wp = min(pabs)
    else:
        weight = np.abs(np.imag(poles) / (np.real(poles) * poles))
        wp, _ = max(zip(pabs, weight), key=lambda x: x[1])

    g0 = _eval_tf(mat_a, mat_b, mat_c, mat_d, 0)
    gwp = _eval_tf(mat_a, mat_b, mat_c, mat_d, 1j * wp)

    sig = []
    for tf in (g0, gwp, mat_d):
        _, s, _ = linalg.svd(tf)
        sig.append(max(s))

    glb = max(sig)
    return glb


def _initial_glb_discrete(az, bz, cz, dz):
    poles, _ = linalg.eig(az)
    phip = np.angle(poles[np.argmax(np.abs(poles))])
    phis = np.array([0.0, phip, np.pi])

    def max_sv(phi):
        tf = _eval_tf(az, bz, cz, dz, np.exp(1j * phi))
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
        Returns the imaginary components of the imaginary values. The list is sorted.
    """
    x_imag = np.imag(x_vals)
    is_imag = np.isclose(1j * x_imag, x_vals, rtol=1e-12, atol=1e-8)
    only_imag = []
    for (is_, xi) in zip(is_imag, x_imag):
        if is_:
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
    is_unit = np.isclose(np.exp(1j * x_phis), x_vals, rtol=1e-12, atol=1e-8)
    only_unit = x_phis[is_unit]
    no_unit = only_unit.shape[0] == 0
    return no_unit, np.sort(only_unit)


def _find_new_lower_bound(wi, mat_a, mat_b, mat_c, mat_d):
    si = []
    for i in range(len(wi) - 1):
        mi = 0.5 * (wi[i] + wi[i + 1])
        gw = _eval_tf(mat_a, mat_b, mat_c, mat_d, 1j * mi)
        _, s, _ = linalg.svd(gw)
        si.append(max(s))
    glb = max(si)
    return glb


def _find_new_lower_bound_discrete(phis, az, bz, cz, dz):
    def max_sv(mi):
        gw = _eval_tf(az, bz, cz, dz, np.exp(1j * mi))
        _, sv, _ = linalg.svd(gw)
        return max(sv)

    mis = np.diff(phis)
    vfunc = np.vectorize(max_sv)
    svs = vfunc(mis)
    glb = max(svs)
    return glb


def norm_hinf_continuous(ac, bc, cc, dc):
    """
    Reference
    ---------
    A fast algorithm to compute the H∞-norm of a transfer function matrix; N.A. Bruinsma and M. Steinbuch;
    Systems & Control Letters, 1990, 14(4) pp. 287 - 293, 10.1016/0167-6911(90)90049-Z
    """
    glb, gub = _initial_glb(ac, bc, cc, dc), 0
    no_imaginary = False
    eps = 1e-8

    while no_imaginary is False:
        g = (1 + 2 * eps) * glb
        hg = _hamiltonian_matrix_continuous(g, ac, bc, cc, dc)
        e, _ = linalg.eig(hg)
        no_imaginary, wi = _robust_no_imaginary(e)
        if no_imaginary is True:
            gub = g
        else:
            glb = _find_new_lower_bound(wi, ac, bc, cc, dc)

    norm = 0.5 * (glb + gub)
    return norm


def norm_hinf_discrete(az, bz, cz, dz):
    """
    Reference
    ---------
    L∞-norm calculation for generalized state space systems in continuous and discrete time; P. M. M. Bongers and
    O. H. Bosgra and M. Steinbuch; 1991 American Control Conference, 10.23919/ACC.1991.4791655

    Returns
    -------
    norm : float
        H∞ norm of the system.
    """
    glb, gub, no_unit, eps = _initial_glb_discrete(az, bz, cz, dz), 0, False, 1e-8

    while no_unit is False:
        g = (1 + 2 * eps) * glb
        m_mat, l_mat = _matrices_discrete(g, az, bz, cz, dz)
        e, _ = linalg.eig(m_mat, l_mat)
        no_unit, phis = _robust_no_unit(e)
        if no_unit is True:
            gub = g
        else:
            glb = _find_new_lower_bound_discrete(phis, az, bz, cz, dz)

    norm = 0.5 * (glb + gub)
    return norm


def norm_h2_continuous(ac, bc, cc):
    """
    Numerically computes the H2 norm of a LTI continuous time system.
    
    Parameters
    ----------
    ac : ndarray
        The state update matrix.
    bc : ndarray
        The input matrix.
    cc : ndarray
        The output matrix.
        
    Returns
    -------
    norm : float
        The H2 norm.
    """
    # A, B, C, D = sys.params
    wo = observability_gramian_continuous(ac, cc)
    norm = np.sqrt(np.trace(bc.T @ wo @ bc))
    return norm


def norm_h2_discrete(az, bz, cz):
    """
    Numerically computes the H2 norm of a LTI discrete time system.
    
    Parameters
    ----------
    az : ndarray
        The state update matrix.
    bz : ndarray
        The input matrix.
    cz : ndarray
        The output matrix.
        
    Returns
    -------
    norm : float
        The H$_2$ norm.
    """
    # if sys.is_delta():
    #     sys = sys.delta2shift()
    # A, B, C, D = sys.params
    wo = observability_gramian_discrete(az, cz)
    norm = np.sqrt(np.trace(bz.T @ wo @ bz))
    return norm


def lqr_continuous(mat_a, mat_b, mat_q, mat_r):
    """
    Solve the continuous time lqr controller.
    
    dx/dt = A x + B u
        
    cost = integral x.T*Q*x + u.T*R*u

    Parameters
    ----------
    mat_a : ndarray
        The system state matrix.
    mat_b : ndarray
        The system input matrix.
    mat_q : ndarray
        The weighting matrix for the states.
    mat_r : ndarray
        The weighting matrix for the control action.
        
    Returns
    -------
    mat_k : ndarray
        The state feedback matrix.
    mat_p : ndarray
        The solution to the Algebraic Ricatti Equation.
    w : ndarray
        The eigenvalues of the closed loop system.
    """
    mat_p = linalg.solve_continuous_are(mat_a, mat_b, mat_q, mat_r)
    mat_r_inv = linalg.inv(mat_r)
    mat_k = mat_r_inv.dot(mat_b.T).dot(mat_p)
    w, _ = linalg.eig(mat_a - mat_b.dot(mat_k))
    return mat_k, mat_p, w


def controllability_gramian_continuous(mat_a, mat_b):
    """
    Calculates the controllabilty gramian of a continuous time LTI system.
    
    Parameters
    ----------
    mat_a : ndarray
        The state matrix.
    mat_b : ndarray
        The input matrix.
        
    Returns
    -------
    mat_wc : ndarray
        The controllability gramian.
    """
    mat_q = -mat_b @ mat_b.T
    mat_wc = linalg.solve_continuous_lyapunov(mat_a, mat_q)
    return mat_wc


def controllability_gramian_discrete(mat_a, mat_b):
    """
    Calculates the controllabilty gramian of a discrete time LTI system.
    
    Parameters
    ----------
    mat_a : ndarray
        The state matrix.
    mat_b : ndarray
        The input matrix.
        
    Returns
    -------
    mat_wc : ndarray
        The controllability gramian.
    """
    mat_q = mat_b @ mat_b.T
    mat_wc = linalg.solve_discrete_lyapunov(mat_a, mat_q)
    return mat_wc


def observability_gramian_continuous(mat_a, mat_c):
    """
    Calculates the observability gramian of a continuous time LTI system.
    
    Parameters
    ----------
    mat_a : ndarray
        The state matrix.
    mat_c : ndarray
        The output matrix.
        
    Returns
    -------
    mat_wo : ndarray
        The observability gramian.
    """
    mat_q = -mat_c.T @ mat_c
    mat_wo = linalg.solve_continuous_lyapunov(mat_a.T, mat_q)
    return mat_wo


def observability_gramian_discrete(mat_a, mat_c):
    """
    Calculates the observability gramian of a discrete time LTI system.
    
    Parameters
    ----------
    mat_a : ndarray
        The state matrix.
    mat_c : ndarray
        The output matrix.
        
    Returns
    -------
    mat_wo : ndarray
        The observability gramian.
    """
    mat_q = mat_c.T @ mat_c
    mat_wo = linalg.solve_discrete_lyapunov(mat_a.T, mat_q)
    return mat_wo


def balanced_realization_discrete(az, bz, cz, dz):
    # if not sys.is_shift():
    #     msg = 'Balanced realization for shift operator only.'
    #     raise ValueError(msg)

    # A, B, C, D = sys.params
    mat_p = controllability_gramian_discrete(az, bz)
    mat_q = observability_gramian_discrete(az, cz)
    mat_r = linalg.cholesky(mat_p, lower=True)
    rtran_qr = mat_r.T @ mat_q @ mat_r
    mat_u, s, _ = linalg.svd(rtran_qr)
    ssqrtsqrt = np.sqrt(np.sqrt(s))
    sigma_sqrt_inv = np.diag(np.reciprocal(ssqrtsqrt))
    # SigmaSqrt = np.diag(np.sqrt(np.sqrt(s)))
    mat_t = mat_r @ mat_u @ sigma_sqrt_inv
    mat_t_inv = linalg.inv(mat_t)
    # mat_t_inv = SigmaSqrt.dot(mat_u.mat_t).dot(linalg.inv(mat_r))
    ab = mat_t_inv @ az @ mat_t
    bb = mat_t_inv @ bz
    cb = cz @ mat_t
    db = dz
    # return StateSpace(ab, bb, cb, db, dt=sys.dt)
    return ab, bb, cb, db
