const RealTimePriceService = require('./real-time-price-service');

async function testPriceService() {
  console.log("🧪 Testing Real-time Price Service...");
  
  const priceService = new RealTimePriceService();
  
  try {
    // Start the service
    await priceService.start();
    
    // Wait for initial price update
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Print prices
    priceService.printPriceSummary();
    
    // Stop the service
    priceService.stop();
    
    console.log("✅ Price service test completed successfully!");
    
  } catch (error) {
    console.error("❌ Price service test failed:", error.message);
  }
}

testPriceService(); 