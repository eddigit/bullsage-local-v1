/**
 * BSTToken Model
 * 
 * Modèle MongoDB pour le système de tokens BST (gamification interne).
 * 
 * @author Jules
 * @date 08/02/2026
 */

const mongoose = require('mongoose');

const TransactionSchema = new mongoose.Schema({
  type: {
    type: String,
    enum: ['mint', 'transfer', 'burn', 'reward', 'spend'],
    required: true
  },
  amount: {
    type: Number,
    required: true
  },
  reason: {
    type: String,
    required: true,
    maxlength: 500
  },
  from: {
    type: String,
    default: null  // User ID source (pour transfers)
  },
  to: {
    type: String,
    default: null  // User ID destination (pour transfers)
  },
  admin: {
    type: String,
    default: null  // Admin qui a effectué l'action (si applicable)
  },
  timestamp: {
    type: Date,
    default: Date.now
  }
});

const BSTTokenSchema = new mongoose.Schema({
  user_id: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  balance: {
    type: Number,
    default: 0,
    min: 0  // Le solde ne peut pas être négatif
  },
  total_earned: {
    type: Number,
    default: 0,
    min: 0
  },
  total_spent: {
    type: Number,
    default: 0,
    min: 0
  },
  transactions: [TransactionSchema],
  created_at: {
    type: Date,
    default: Date.now
  },
  updated_at: {
    type: Date,
    default: Date.now
  }
});

// Index sur timestamp des transactions pour performances
BSTTokenSchema.index({ 'transactions.timestamp': -1 });

// Middleware pre-save pour mettre à jour updated_at
BSTTokenSchema.pre('save', function(next) {
  this.updated_at = Date.now();
  next();
});

// Méthode pour ajouter une transaction et mettre à jour le solde
BSTTokenSchema.methods.addTransaction = function(type, amount, reason, options = {}) {
  const transaction = {
    type,
    amount,
    reason,
    from: options.from || null,
    to: options.to || null,
    admin: options.admin || null,
    timestamp: new Date()
  };

  this.transactions.push(transaction);

  // Mettre à jour le solde
  this.balance += amount;

  // Mettre à jour total_earned ou total_spent
  if (amount > 0) {
    this.total_earned += amount;
  } else {
    this.total_spent += Math.abs(amount);
  }

  return transaction;
};

// Méthode statique pour créer ou récupérer un compte BST
BSTTokenSchema.statics.getOrCreate = async function(user_id) {
  let account = await this.findOne({ user_id });
  
  if (!account) {
    account = new this({
      user_id,
      balance: 0,
      total_earned: 0,
      total_spent: 0,
      transactions: []
    });
    await account.save();
  }
  
  return account;
};

// Méthode statique pour obtenir le leaderboard
BSTTokenSchema.statics.getLeaderboard = async function(limit = 100) {
  return this.find()
    .sort({ balance: -1 })
    .limit(limit)
    .select('user_id balance total_earned total_spent');
};

// Méthode statique pour obtenir les stats globales
BSTTokenSchema.statics.getGlobalStats = async function() {
  const totalUsers = await this.countDocuments();
  
  const aggregation = await this.aggregate([
    {
      $group: {
        _id: null,
        total_supply: { $sum: '$balance' },
        avg_balance: { $avg: '$balance' },
        max_balance: { $max: '$balance' }
      }
    }
  ]);

  const stats = aggregation[0] || { total_supply: 0, avg_balance: 0, max_balance: 0 };
  
  const topHolder = await this.findOne().sort({ balance: -1 }).select('user_id balance');

  return {
    total_supply: stats.total_supply,
    total_users: totalUsers,
    avg_balance: Math.round(stats.avg_balance),
    top_holder: topHolder ? {
      user_id: topHolder.user_id,
      balance: topHolder.balance
    } : null
  };
};

const BSTToken = mongoose.model('BSTToken', BSTTokenSchema);

module.exports = BSTToken;
