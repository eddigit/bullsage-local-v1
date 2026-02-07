/**
 * BST Token Routes
 * 
 * Routes pour le système de tokens BST.
 * 
 * @author Jules
 * @date 08/02/2026
 */

const express = require('express');
const router = express.Router();
const bstController = require('../../controllers/bst/bstController');
const { authenticate } = require('../../middleware/auth');
const { requireAdmin } = require('../../middleware/bst/adminMiddleware');

// Routes publiques (avec auth)
router.get('/balance/:userId', authenticate, bstController.getBalance);
router.get('/history/:userId', authenticate, bstController.getHistory);
router.get('/leaderboard', bstController.getLeaderboard);  // Public

// Routes utilisateur (avec auth)
router.post('/transfer', authenticate, bstController.transfer);
router.post('/spend', authenticate, bstController.spend);

// Routes admin uniquement
router.post('/mint', authenticate, requireAdmin, bstController.mint);
router.post('/burn', authenticate, requireAdmin, bstController.burn);
router.post('/reward', authenticate, requireAdmin, bstController.reward);
router.get('/stats', authenticate, requireAdmin, bstController.getStats);

module.exports = router;
