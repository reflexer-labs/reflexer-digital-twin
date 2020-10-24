function getRandomPrices(steps, minPrice, maxPrice) {
  var normalPrices = [];
  var scaledPrices = [];
  var newPrice;

  for (var i = 0; i < steps; i++) {
    newPrice = (Math.random() * (maxPrice - minPrice) + minPrice);
    normalPrices.push(newPrice);
    newPrice = newPrice.toFixed(10);
    newPrice = newPrice.toString().replace(".", "");
    scaledPrices.push(newPrice);
  }

  // console.dir(normalPrices, {'maxArrayLength': null});

  return [normalPrices, scaledPrices];
}

module.exports = {
    getRandomPrices
}
