/**
 * Bull Sage - Frontend Logging Service
 * =====================================
 *
 * Centralized logging for the frontend application.
 * Provides consistent logging with timestamps and context.
 *
 * Usage:
 *   import { logger } from '@/lib/logger';
 *   logger.info('User logged in', { userId: '123' });
 *   logger.error('API call failed', { endpoint: '/api/market' });
 */

const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
};

// Set minimum log level (can be configured via environment)
const MIN_LOG_LEVEL = process.env.NODE_ENV === 'production' ? LOG_LEVELS.WARN : LOG_LEVELS.DEBUG;

// Prefix for all log messages
const PREFIX = '[Bull Sage]';

/**
 * Format a log message with timestamp and context
 */
function formatMessage(level, message, context) {
  const timestamp = new Date().toISOString();
  const contextStr = context ? ` | ${JSON.stringify(context)}` : '';
  return `${PREFIX} [${timestamp}] [${level}] ${message}${contextStr}`;
}

/**
 * Store recent logs in memory for debugging
 */
const recentLogs = [];
const MAX_RECENT_LOGS = 100;

function storeLog(level, message, context) {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    context,
  };
  recentLogs.push(entry);
  if (recentLogs.length > MAX_RECENT_LOGS) {
    recentLogs.shift();
  }
}

/**
 * Logger object with methods for each log level
 */
export const logger = {
  /**
   * Debug level - verbose information for development
   */
  debug(message, context = null) {
    if (LOG_LEVELS.DEBUG >= MIN_LOG_LEVEL) {
      console.debug(formatMessage('DEBUG', message, context));
      storeLog('DEBUG', message, context);
    }
  },

  /**
   * Info level - general information
   */
  info(message, context = null) {
    if (LOG_LEVELS.INFO >= MIN_LOG_LEVEL) {
      console.log(formatMessage('INFO', message, context));
      storeLog('INFO', message, context);
    }
  },

  /**
   * Warn level - potential issues
   */
  warn(message, context = null) {
    if (LOG_LEVELS.WARN >= MIN_LOG_LEVEL) {
      console.warn(formatMessage('WARN', message, context));
      storeLog('WARN', message, context);
    }
  },

  /**
   * Error level - errors that need attention
   */
  error(message, context = null) {
    if (LOG_LEVELS.ERROR >= MIN_LOG_LEVEL) {
      console.error(formatMessage('ERROR', message, context));
      storeLog('ERROR', message, context);
    }
  },

  /**
   * Log an API call result
   */
  api(endpoint, success, responseTime = null, error = null) {
    const context = {
      endpoint,
      success,
      ...(responseTime && { responseTime: `${responseTime}ms` }),
      ...(error && { error: error.message || error }),
    };

    if (success) {
      this.info(`API call successful: ${endpoint}`, context);
    } else {
      this.error(`API call failed: ${endpoint}`, context);
    }
  },

  /**
   * Log a user action
   */
  action(action, details = null) {
    this.info(`User action: ${action}`, details);
  },

  /**
   * Log a page view
   */
  pageView(pageName) {
    this.info(`Page view: ${pageName}`);
  },

  /**
   * Get recent logs (useful for debugging)
   */
  getRecentLogs() {
    return [...recentLogs];
  },

  /**
   * Clear recent logs
   */
  clearLogs() {
    recentLogs.length = 0;
  },

  /**
   * Export logs as JSON string
   */
  exportLogs() {
    return JSON.stringify(recentLogs, null, 2);
  },
};

// Make logger available on window for debugging in console
if (typeof window !== 'undefined') {
  window.bullsageLogger = logger;
}

export default logger;
