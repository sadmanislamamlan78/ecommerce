/**
 * Shop page — price range sliders
 */
(function () {
    'use strict';

    const minSlider = document.getElementById('minPriceSlider');
    const maxSlider = document.getElementById('maxPriceSlider');
    const minInput = document.getElementById('minPriceInput');
    const maxInput = document.getElementById('maxPriceInput');
    const minLabel = document.getElementById('minPriceLabel');
    const maxLabel = document.getElementById('maxPriceLabel');

    if (!minSlider || !maxSlider) return;

    const floor = parseInt(minSlider.min, 10);
    const ceiling = parseInt(maxSlider.max, 10);

    function sync() {
        let minVal = parseInt(minSlider.value, 10);
        let maxVal = parseInt(maxSlider.value, 10);

        if (minVal > maxVal) {
            if (this === minSlider) {
                minVal = maxVal;
                minSlider.value = minVal;
            } else {
                maxVal = minVal;
                maxSlider.value = maxVal;
            }
        }

        minVal = Math.max(floor, Math.min(minVal, ceiling));
        maxVal = Math.max(floor, Math.min(maxVal, ceiling));

        minInput.value = minVal;
        maxInput.value = maxVal;
        minLabel.textContent = minVal;
        maxLabel.textContent = maxVal;
    }

    minSlider.addEventListener('input', sync);
    maxSlider.addEventListener('input', sync);

})();
