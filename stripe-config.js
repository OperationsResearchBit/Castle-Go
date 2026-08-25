/**
 * Stripe Configuration for Castle Go and other games
 * 
 * SECURITY WARNING: This file contains your Stripe publishable key (public).
 * Publishable keys are safe to expose in client-side code.
 * NEVER commit your Stripe secret key to version control.
 * 
 * To use this file:
 * 1. Replace YOUR_STRIPE_PUBLISHABLE_KEY with your actual Stripe key
 * 2. Load this file BEFORE your PaymentWidget script
 * 3. The config will be available as window.STRIPE_CONFIG
 */

window.STRIPE_CONFIG = {
    // Your Stripe publishable key (found in Stripe Dashboard → Developers → API Keys)
    publishableKey: 'pk_test_YOUR_STRIPE_PUBLISHABLE_KEY_HERE',
    
    // Game-specific configuration
    gameId: 'castle-go',
    gameName: 'Castle Go',
    
    // PaymentWidget configuration
    paymentWidgetConfig: {
        container: '#payment-widget-container',
        features: ['premium_pass', 'battle_pass', 'supporter'],
        locale: 'en',
    },
    
    // Product pricing (in cents)
    products: {
        premium_pass: {
            name: 'Premium Pass',
            price: 999, // $9.99
            duration: 'monthly',
            description: 'Unlock expansion maps, custom colors & avatars, ad-free play'
        },
        battle_pass: {
            name: 'Battle Pass',
            price: 1299, // $12.99
            duration: 'seasonal',
            description: 'Exclusive rewards and cosmetics'
        },
        supporter: {
            name: 'Supporter Pack',
            price: 4999, // $49.99
            duration: 'one-time',
            description: 'Support development + exclusive perks'
        }
    },
    
    // Callback functions
    onPaymentSuccess: (purchase) => {
        console.log('Payment successful:', purchase);
        // Unlock premium features based on purchase
        if (purchase.productId === 'premium_pass') {
            window.enablePremiumFeatures();
        }
    },
    
    onPaymentError: (error) => {
        console.error('Payment error:', error);
        alert('Payment failed. Please try again.');
    },
    
    // Feature unlock mapping
    featureUnlocks: {
        premium_pass: ['expansion_maps', 'custom_colors', 'avatars', 'ad_free'],
        battle_pass: ['seasonal_rewards', 'cosmetics'],
        supporter: ['all_features', 'supporter_badge']
    }
};

/**
 * SETUP INSTRUCTIONS:
 * 
 * 1. Get your Stripe key:
 *    - Go to https://dashboard.stripe.com/
 *    - Click "Developers" in the left sidebar
 *    - Copy your "Publishable key" (starts with pk_test_ or pk_live_)
 *    - Paste it above where it says YOUR_STRIPE_PUBLISHABLE_KEY_HERE
 * 
 * 2. Update the index.html to load this file:
 *    <script src="stripe-config.js"></script>
 *    <script src="https://operationsresearchbit.github.io/PaymentsCart/payment-widget.js"></script>
 * 
 * 3. Initialize PaymentWidget in your game:
 *    PaymentWidget.init({
 *        ...window.STRIPE_CONFIG.paymentWidgetConfig,
 *        gameId: window.STRIPE_CONFIG.gameId,
 *        onSuccess: window.STRIPE_CONFIG.onPaymentSuccess,
 *        onError: window.STRIPE_CONFIG.onPaymentError
 *    });
 * 
 * 4. To use in other games:
 *    - Copy this file to each game's root directory
 *    - Update gameId and gameName for each game
 *    - Load it before PaymentWidget in index.html
 *    - No other changes needed
 */
