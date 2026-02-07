/**
 * Admin Middleware
 * 
 * Middleware pour vérifier que l'utilisateur a le rôle admin.
 * 
 * @author Jules
 * @date 08/02/2026
 */

/**
 * Middleware pour vérifier que l'utilisateur est admin
 */
exports.requireAdmin = (req, res, next) => {
  // req.user est défini par le middleware authenticate
  if (!req.user) {
    return res.status(401).json({
      success: false,
      message: 'Authentication required'
    });
  }

  if (req.user.role !== 'admin') {
    return res.status(403).json({
      success: false,
      message: 'Admin access required'
    });
  }

  next();
};
