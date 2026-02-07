/**
 * BST Token Controller
 * 
 * Contrôleur pour gérer les opérations sur les tokens BST.
 * 
 * @author Jules
 * @date 08/02/2026
 */

const BSTToken = require('../../models/bst/BSTToken');

/**
 * GET /api/bst/balance/:userId
 * Récupérer le solde BST d'un utilisateur
 */
exports.getBalance = async (req, res) => {
  try {
    const { userId } = req.params;

    // Vérification : user ne peut voir que son propre solde (sauf admin)
    if (req.user.role !== 'admin' && req.user.id !== userId) {
      return res.status(403).json({
        success: false,
        message: 'You can only view your own balance'
      });
    }

    const account = await BSTToken.getOrCreate(userId);

    res.json({
      success: true,
      user_id: account.user_id,
      balance: account.balance,
      total_earned: account.total_earned,
      total_spent: account.total_spent
    });
  } catch (error) {
    console.error('Error getting balance:', error);
    res.status(500).json({
      success: false,
      message: 'Error getting balance',
      error: error.message
    });
  }
};

/**
 * GET /api/bst/history/:userId
 * Récupérer l'historique des transactions BST
 */
exports.getHistory = async (req, res) => {
  try {
    const { userId } = req.params;
    const limit = parseInt(req.query.limit) || 50;
    const offset = parseInt(req.query.offset) || 0;

    // Vérification : user ne peut voir que son propre historique (sauf admin)
    if (req.user.role !== 'admin' && req.user.id !== userId) {
      return res.status(403).json({
        success: false,
        message: 'You can only view your own history'
      });
    }

    const account = await BSTToken.findOne({ user_id: userId });

    if (!account) {
      return res.json({
        success: true,
        user_id: userId,
        transactions: []
      });
    }

    // Trier par timestamp décroissant et paginer
    const transactions = account.transactions
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(offset, offset + limit);

    res.json({
      success: true,
      user_id: userId,
      transactions,
      total_count: account.transactions.length
    });
  } catch (error) {
    console.error('Error getting history:', error);
    res.status(500).json({
      success: false,
      message: 'Error getting history',
      error: error.message
    });
  }
};

/**
 * POST /api/bst/mint
 * Créer des tokens BST et les attribuer à un utilisateur (admin only)
 */
exports.mint = async (req, res) => {
  try {
    const { user_id, amount, reason } = req.body;

    // Validation
    if (!user_id || !amount || !reason) {
      return res.status(400).json({
        success: false,
        message: 'user_id, amount, and reason are required'
      });
    }

    if (amount <= 0) {
      return res.status(400).json({
        success: false,
        message: 'Amount must be positive'
      });
    }

    const account = await BSTToken.getOrCreate(user_id);

    const transaction = account.addTransaction('mint', amount, reason, {
      admin: req.user.id
    });

    await account.save();

    res.json({
      success: true,
      new_balance: account.balance,
      transaction_id: transaction._id
    });
  } catch (error) {
    console.error('Error minting tokens:', error);
    res.status(500).json({
      success: false,
      message: 'Error minting tokens',
      error: error.message
    });
  }
};

/**
 * POST /api/bst/transfer
 * Transférer des tokens BST entre utilisateurs
 */
exports.transfer = async (req, res) => {
  try {
    const { from_user_id, to_user_id, amount, reason } = req.body;

    // Validation
    if (!from_user_id || !to_user_id || !amount || !reason) {
      return res.status(400).json({
        success: false,
        message: 'from_user_id, to_user_id, amount, and reason are required'
      });
    }

    if (amount <= 0) {
      return res.status(400).json({
        success: false,
        message: 'Amount must be positive'
      });
    }

    if (from_user_id === to_user_id) {
      return res.status(400).json({
        success: false,
        message: 'Cannot transfer to yourself'
      });
    }

    // Vérification : user ne peut transférer que depuis son propre compte (sauf admin)
    if (req.user.role !== 'admin' && req.user.id !== from_user_id) {
      return res.status(403).json({
        success: false,
        message: 'You can only transfer from your own account'
      });
    }

    const fromAccount = await BSTToken.getOrCreate(from_user_id);
    const toAccount = await BSTToken.getOrCreate(to_user_id);

    // Vérifier le solde
    if (fromAccount.balance < amount) {
      return res.status(400).json({
        success: false,
        message: 'Insufficient balance'
      });
    }

    // Débiter le compte source
    fromAccount.addTransaction('transfer', -amount, reason, {
      from: from_user_id,
      to: to_user_id
    });

    // Créditer le compte destination
    toAccount.addTransaction('transfer', amount, reason, {
      from: from_user_id,
      to: to_user_id
    });

    await fromAccount.save();
    await toAccount.save();

    res.json({
      success: true,
      from_balance: fromAccount.balance,
      to_balance: toAccount.balance
    });
  } catch (error) {
    console.error('Error transferring tokens:', error);
    res.status(500).json({
      success: false,
      message: 'Error transferring tokens',
      error: error.message
    });
  }
};

/**
 * POST /api/bst/burn
 * Détruire des tokens BST (retirer du solde utilisateur) (admin only)
 */
exports.burn = async (req, res) => {
  try {
    const { user_id, amount, reason } = req.body;

    // Validation
    if (!user_id || !amount || !reason) {
      return res.status(400).json({
        success: false,
        message: 'user_id, amount, and reason are required'
      });
    }

    if (amount <= 0) {
      return res.status(400).json({
        success: false,
        message: 'Amount must be positive'
      });
    }

    const account = await BSTToken.getOrCreate(user_id);

    // Vérifier le solde
    if (account.balance < amount) {
      return res.status(400).json({
        success: false,
        message: 'Insufficient balance to burn'
      });
    }

    account.addTransaction('burn', -amount, reason, {
      admin: req.user.id
    });

    await account.save();

    res.json({
      success: true,
      new_balance: account.balance
    });
  } catch (error) {
    console.error('Error burning tokens:', error);
    res.status(500).json({
      success: false,
      message: 'Error burning tokens',
      error: error.message
    });
  }
};

/**
 * POST /api/bst/reward
 * Récompenser un utilisateur avec des tokens BST
 */
exports.reward = async (req, res) => {
  try {
    const { user_id, amount, reason } = req.body;

    // Validation
    if (!user_id || !amount || !reason) {
      return res.status(400).json({
        success: false,
        message: 'user_id, amount, and reason are required'
      });
    }

    if (amount <= 0) {
      return res.status(400).json({
        success: false,
        message: 'Amount must be positive'
      });
    }

    const account = await BSTToken.getOrCreate(user_id);

    const transaction = account.addTransaction('reward', amount, reason, {
      admin: req.user.role === 'admin' ? req.user.id : 'system'
    });

    await account.save();

    res.json({
      success: true,
      new_balance: account.balance,
      transaction_id: transaction._id
    });
  } catch (error) {
    console.error('Error rewarding tokens:', error);
    res.status(500).json({
      success: false,
      message: 'Error rewarding tokens',
      error: error.message
    });
  }
};

/**
 * POST /api/bst/spend
 * Dépenser des tokens BST (débloquer feature, etc.)
 */
exports.spend = async (req, res) => {
  try {
    const { user_id, amount, reason } = req.body;

    // Validation
    if (!user_id || !amount || !reason) {
      return res.status(400).json({
        success: false,
        message: 'user_id, amount, and reason are required'
      });
    }

    if (amount <= 0) {
      return res.status(400).json({
        success: false,
        message: 'Amount must be positive'
      });
    }

    // Vérification : user ne peut dépenser que depuis son propre compte (sauf admin)
    if (req.user.role !== 'admin' && req.user.id !== user_id) {
      return res.status(403).json({
        success: false,
        message: 'You can only spend from your own account'
      });
    }

    const account = await BSTToken.getOrCreate(user_id);

    // Vérifier le solde
    if (account.balance < amount) {
      return res.status(400).json({
        success: false,
        message: 'Insufficient balance'
      });
    }

    account.addTransaction('spend', -amount, reason);

    await account.save();

    res.json({
      success: true,
      new_balance: account.balance
    });
  } catch (error) {
    console.error('Error spending tokens:', error);
    res.status(500).json({
      success: false,
      message: 'Error spending tokens',
      error: error.message
    });
  }
};

/**
 * GET /api/bst/leaderboard
 * Récupérer le classement des utilisateurs par balance BST
 */
exports.getLeaderboard = async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 100;

    const leaderboard = await BSTToken.getLeaderboard(limit);

    // Ajouter le rank
    const leaderboardWithRank = leaderboard.map((account, index) => ({
      user_id: account.user_id,
      balance: account.balance,
      total_earned: account.total_earned,
      total_spent: account.total_spent,
      rank: index + 1
    }));

    res.json({
      success: true,
      leaderboard: leaderboardWithRank
    });
  } catch (error) {
    console.error('Error getting leaderboard:', error);
    res.status(500).json({
      success: false,
      message: 'Error getting leaderboard',
      error: error.message
    });
  }
};

/**
 * GET /api/bst/stats
 * Statistiques globales du système BST (admin only)
 */
exports.getStats = async (req, res) => {
  try {
    const stats = await BSTToken.getGlobalStats();

    res.json({
      success: true,
      ...stats
    });
  } catch (error) {
    console.error('Error getting stats:', error);
    res.status(500).json({
      success: false,
      message: 'Error getting stats',
      error: error.message
    });
  }
};
