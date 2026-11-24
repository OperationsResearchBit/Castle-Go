/**
 * PaymentWidget.js v2 - Shared Payment Integration with Tiered Subscriptions
 * 
 * Features:
 * - Per-game premium passes (monthly & yearly)
 * - Bundle option: 1 month access to all 4 games at 2x individual price
 * - localStorage persistence
 * - Stripe-ready with fallback demo mode
 */

const PaymentWidget = (() => {
  let config = {};
  let stripe = null;
  let currentUser = null;

  // Game Premium Passes
  const gameSubscriptions = {
    'swimcraft': {
      name: 'Swimcraft Premium',
      color: '#FF6B9D',
      monthly: { id: 'swimcraft_month', name: 'Monthly', price: 4.99, duration: 'month' },
      yearly: { id: 'swimcraft_year', name: 'Yearly', price: 39.99, duration: 'year' }
    },
    'castle-go': {
      name: 'Castle-Go Premium',
      color: '#FFD700',
      monthly: { id: 'castlego_month', name: 'Monthly', price: 4.99, duration: 'month' },
      yearly: { id: 'castlego_year', name: 'Yearly', price: 39.99, duration: 'year' }
    },
    'survival-rpg': {
      name: 'Survival Premium',
      color: '#DC143C',
      monthly: { id: 'survival_month', name: 'Monthly', price: 4.99, duration: 'month' },
      yearly: { id: 'survival_year', name: 'Yearly', price: 39.99, duration: 'year' }
    },
    'friction-wars': {
      name: 'Friction Wars Premium',
      color: '#00BFFF',
      monthly: { id: 'friction_month', name: 'Monthly', price: 4.99, duration: 'month' },
      yearly: { id: 'friction_year', name: 'Yearly', price: 39.99, duration: 'year' }
    }
  };

  const bundleOption = {
    id: 'bundle_all_month',
    name: '🎮 Bundle: All 4 Games (1 Month)',
    price: 9.99, // 2x price of single game
    duration: 'month',
    games: ['swimcraft', 'castle-go', 'survival-rpg', 'friction-wars'],
    savings: 'Save $9.96!'
  };

  /**
   * Initialize the payment widget
   */
  function init(options) {
    config = {
      gameId: options.gameId,
      gameName: options.gameName || 'Game',
      stripePublishableKey: options.stripePublishableKey || 'pk_test_51U8leVCXVSFGhpL2Dtgpgw9iRkJLvsKnO9hRI5lgw21VnEpDmlaASl2zk53pe7gPzNScs1i6qTp7DsFmITx4d6T700tm8ONdWC',
      onSuccess: options.onSuccess || (() => {}),
      container: options.container || '#payment-widget-container',
      showBundle: options.showBundle !== false // Show bundle by default
    };

    // Initialize Stripe if key is provided
    if (config.stripePublishableKey && config.stripePublishableKey.startsWith('pk_')) {
      stripe = Stripe(config.stripePublishableKey);
    }

    loadUser();
    renderWidget();
  }

  /**
   * Load user from localStorage or create guest
   */
  function loadUser() {
    const stored = localStorage.getItem('arcade_user');
    if (stored) {
      currentUser = JSON.parse(stored);
    } else {
      currentUser = {
        uid: 'user_' + Math.random().toString(36).substr(2, 9),
        email: null,
        subscriptions: [] // Array of active subscriptions
      };
      localStorage.setItem('arcade_user', JSON.stringify(currentUser));
    }
  }

  /**
   * Check if user has active subscription
   */
  function hasSubscription(gameId, type = 'any') {
    return currentUser.subscriptions.some(sub => {
      const isGame = sub.gameId === gameId || (sub.gameIds && sub.gameIds.includes(gameId));
      const isActive = new Date(sub.expiresAt) > new Date();
      
      if (type === 'any') return isGame && isActive;
      if (type === 'month') return isGame && isActive && sub.duration === 'month';
      if (type === 'year') return isGame && isActive && sub.duration === 'year';
      return false;
    });
  }

  /**
   * Get subscription details
   */
  function getSubscription(gameId) {
    return currentUser.subscriptions.find(sub => {
      const isGame = sub.gameId === gameId || (sub.gameIds && sub.gameIds.includes(gameId));
      const isActive = new Date(sub.expiresAt) > new Date();
      return isGame && isActive;
    });
  }

  /**
   * Render the payment widget UI
   */
  function renderWidget() {
    const container = document.querySelector(config.container);
    if (!container) {
      console.error('Payment widget container not found:', config.container);
      return;
    }

    const gameData = gameSubscriptions[config.gameId];
    if (!gameData) {
      console.error('Unknown game ID:', config.gameId);
      return;
    }

    const hasMonth = hasSubscription(config.gameId, 'month');
    const hasYear = hasSubscription(config.gameId, 'year');
    const sub = getSubscription(config.gameId);

    const html = `
      <div style="font-family: sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; padding: 20px; border-radius: 12px; max-width: 420px; border: 2px solid ${gameData.color}40;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
          <h3 style="margin: 0; color: ${gameData.color}; font-size: 1.2em;">${gameData.name}</h3>
          ${sub ? `<span style="background: #2ecc71; color: #fff; padding: 4px 10px; border-radius: 20px; font-size: 0.75em; font-weight: bold;">✓ ACTIVE</span>` : ''}
        </div>

        ${sub ? `
          <div style="background: rgba(46, 204, 113, 0.1); border-left: 3px solid #2ecc71; padding: 10px; border-radius: 6px; margin-bottom: 15px; font-size: 0.85em;">
            <strong>Active until:</strong> ${new Date(sub.expiresAt).toLocaleDateString()}<br>
            <strong>Plan:</strong> ${sub.duration === 'month' ? '📅 Monthly' : '📆 Yearly'}
          </div>
        ` : ''}

        <!-- SUBSCRIPTION OPTIONS -->
        <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; margin-bottom: 15px;">
          <div style="font-size: 0.85em; font-weight: bold; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px;">Premium Plans:</div>
          
          <!-- MONTHLY -->
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 6px; margin-bottom: 8px; border: 2px solid ${hasMonth ? '#2ecc71' : 'transparent'};">
            <div>
              <strong style="display: block; margin-bottom: 2px;">📅 Monthly Pass</strong>
              <span style="font-size: 0.8em; color: #aaa;">Renews automatically</span>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 1.2em; font-weight: bold; color: ${gameData.color};">$${gameData.monthly.price}</div>
              <div style="font-size: 0.75em; color: #aaa;">/month</div>
              ${hasMonth ? `
                <button onclick="PaymentWidget.manageSubscription('${config.gameId}')" style="background: #2ecc71; color: #000; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75em; font-weight: bold; margin-top: 4px;">Manage</button>
              ` : `
                <button onclick="PaymentWidget.purchase('${gameData.monthly.id}')" style="background: ${gameData.color}; color: #000; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75em; font-weight: bold; margin-top: 4px;">Subscribe</button>
              `}
            </div>
          </div>

          <!-- YEARLY -->
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 6px; margin-bottom: 8px; border: 2px solid ${hasYear ? '#2ecc71' : 'transparent'};">
            <div>
              <strong style="display: block; margin-bottom: 2px;">📆 Yearly Pass</strong>
              <span style="font-size: 0.8em; color: #aaa; display: block;">Best value! Save $20</span>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 1.2em; font-weight: bold; color: ${gameData.color};">$${gameData.yearly.price}</div>
              <div style="font-size: 0.75em; color: #aaa;">/year</div>
              ${hasYear ? `
                <button onclick="PaymentWidget.manageSubscription('${config.gameId}')" style="background: #2ecc71; color: #000; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75em; font-weight: bold; margin-top: 4px;">Manage</button>
              ` : `
                <button onclick="PaymentWidget.purchase('${gameData.yearly.id}')" style="background: ${gameData.color}; color: #000; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75em; font-weight: bold; margin-top: 4px;">Subscribe</button>
              `}
            </div>
          </div>
        </div>

        <!-- BUNDLE OFFER (only show on games, not on bundle page) -->
        ${config.showBundle && config.gameId !== 'bundle' ? `
          <div style="background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); padding: 12px; border-radius: 8px; margin-bottom: 12px; border: 2px solid #FFD700;">
            <div style="color: #000; font-weight: bold; margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
              🎮 ${bundleOption.name}
            </div>
            <div style="color: #000; font-size: 0.9em; margin-bottom: 8px;">
              Access all 4 games for 1 month.<br>
              <strong style="color: #2ecc71;">${bundleOption.savings}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="color: #000; font-size: 1.3em; font-weight: bold;">$${bundleOption.price}</span>
              <button onclick="PaymentWidget.purchase('${bundleOption.id}')" style="background: #000; color: #FFD700; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold;">Get Bundle</button>
            </div>
          </div>
        ` : ''}

        <div style="font-size: 12px; color: #95a5a6; text-align: center; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1);">
          💳 Secure payments powered by Stripe
        </div>
      </div>
    `;

    container.innerHTML = html;
    // Make PaymentWidget globally available for onclick handlers
    window.PaymentWidget = PaymentWidget;
  }

  /**
   * Process a purchase
   */
  async function purchase(subscriptionId) {
    let subscription = null;
    let isBundle = false;

    // Find subscription details
    const gameData = gameSubscriptions[config.gameId];
    if (subscriptionId === bundleOption.id) {
      subscription = bundleOption;
      isBundle = true;
    } else if (gameData?.monthly.id === subscriptionId) {
      subscription = gameData.monthly;
    } else if (gameData?.yearly.id === subscriptionId) {
      subscription = gameData.yearly;
    }

    if (!subscription) {
      console.error('Unknown subscription:', subscriptionId);
      return;
    }

    try {
      // Calculate expiry date
      const now = new Date();
      const expiresAt = new Date(now);
      if (subscription.duration === 'month') {
        expiresAt.setMonth(expiresAt.getMonth() + 1);
      } else if (subscription.duration === 'year') {
        expiresAt.setFullYear(expiresAt.getFullYear() + 1);
      }

      // Create subscription record
      const sub = {
        id: subscriptionId,
        gameId: config.gameId,
        gameIds: isBundle ? bundleOption.games : undefined,
        name: subscription.name,
        price: subscription.price,
        duration: subscription.duration,
        purchasedAt: now.toISOString(),
        expiresAt: expiresAt.toISOString(),
        isBundle: isBundle
      };

      // For bundle: remove other game subscriptions if they're monthly
      if (isBundle) {
        currentUser.subscriptions = currentUser.subscriptions.filter(s => {
          // Keep yearly subscriptions, remove monthly ones for bundled games
          if (bundleOption.games.includes(s.gameId) && s.duration === 'month') {
            return false;
          }
          return true;
        });
      }

      // Add new subscription
      currentUser.subscriptions.push(sub);
      localStorage.setItem('arcade_user', JSON.stringify(currentUser));

      // Trigger callback
      config.onSuccess({
        gameId: config.gameId,
        subscription: sub,
        timestamp: Date.now(),
        user: currentUser
      });

      // Show success message
      alert(`✓ ${isBundle ? 'Bundle' : subscription.name} activated!\nValid until: ${expiresAt.toLocaleDateString()}`);

      // Re-render
      renderWidget();

    } catch (error) {
      console.error('Purchase error:', error);
      alert('✗ Payment failed: ' + error.message);
    }
  }

  /**
   * Manage subscription (cancel, upgrade, etc.)
   */
  function manageSubscription(gameId) {
    const sub = getSubscription(gameId);
    if (!sub) return;

    const action = confirm(
      `Current subscription: ${sub.name}\nExpires: ${new Date(sub.expiresAt).toLocaleDateString()}\n\nCancel this subscription?`
    );

    if (action) {
      currentUser.subscriptions = currentUser.subscriptions.filter(s => s.id !== sub.id);
      localStorage.setItem('arcade_user', JSON.stringify(currentUser));
      renderWidget();
    }
  }

  /**
   * Check subscription verification (for game logic)
   */
  function verify(gameId) {
    const sub = getSubscription(gameId);
    if (sub) {
      return {
        valid: true,
        subscription: sub,
        expiresAt: sub.expiresAt,
        daysRemaining: Math.ceil((new Date(sub.expiresAt) - new Date()) / (1000 * 60 * 60 * 24))
      };
    }
    return { valid: false };
  }

  /**
   * Get all active subscriptions
   */
  function getSubscriptions() {
    return currentUser.subscriptions.filter(sub => new Date(sub.expiresAt) > new Date());
  }

  /**
   * Get user profile
   */
  function getUser() {
    return {
      uid: currentUser.uid,
      email: currentUser.email,
      subscriptions: getSubscriptions().length,
      totalSpent: getSubscriptions().reduce((sum, sub) => sum + sub.price, 0)
    };
  }

  // Public API
  return {
    init,
    purchase,
    manageSubscription,
    verify,
    getSubscriptions,
    getUser,
    hasSubscription
  };
})();

// Make available globally
if (typeof window !== 'undefined') {
  window.PaymentWidget = PaymentWidget;
}
