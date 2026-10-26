/**
 * Electricity Bill Prediction System - Frontend JavaScript
 * Handles preset filling, live bill estimation preview, and interaction helpers.
 */

document.addEventListener("DOMContentLoaded", function () {
    // 1. Preset Fill Buttons on Prediction Form
    const presetButtons = document.querySelectorAll("[data-preset]");
    presetButtons.forEach(button => {
        button.addEventListener("click", function () {
            const presetType = this.getAttribute("data-preset");
            applyPreset(presetType);
        });
    });

    // 2. Real-time Live Bill Preview
    const dailyInput = document.getElementById("average_daily_consumption_kwh");
    const prevInput = document.getElementById("previous_month_consumption_kwh");
    const daysInput = document.getElementById("billing_days");
    const tariffInput = document.getElementById("tariff_per_kwh");
    const fixedInput = document.getElementById("fixed_charges");
    const addChargeInput = document.getElementById("additional_charge_percentage");

    const livePreviewContainer = document.getElementById("live-bill-preview");
    const liveKwhEl = document.getElementById("live-kwh");
    const liveBillEl = document.getElementById("live-bill");

    function updateLivePreview() {
        if (!dailyInput || !daysInput || !tariffInput || !fixedInput || !addChargeInput) return;

        const daily = parseFloat(dailyInput.value) || 0;
        const days = parseFloat(daysInput.value) || 0;
        const tariff = parseFloat(tariffInput.value) || 0;
        const fixed = parseFloat(fixedInput.value) || 0;
        const pct = parseFloat(addChargeInput.value) || 0;

        if (daily > 0 && days > 0 && tariff >= 0) {
            // Rough baseline estimate: daily * days
            const approxKwh = (daily * days);
            const energyCharge = approxKwh * tariff;
            const surcharges = energyCharge * (pct / 100.0);
            const approxTotal = energyCharge + fixed + surcharges;

            if (livePreviewContainer) livePreviewContainer.classList.remove("d-none");
            if (liveKwhEl) liveKwhEl.textContent = approxKwh.toFixed(1) + " kWh (baseline)";
            if (liveBillEl) liveBillEl.textContent = "₹ " + approxTotal.toFixed(2);
        } else {
            if (livePreviewContainer) livePreviewContainer.classList.add("d-none");
        }
    }

    const formInputs = [dailyInput, prevInput, daysInput, tariffInput, fixedInput, addChargeInput];
    formInputs.forEach(input => {
        if (input) {
            input.addEventListener("input", updateLivePreview);
        }
    });

    // Run initial update if form is already filled
    updateLivePreview();

    // 3. Delete Confirmation Modal
    const deleteModalEl = document.getElementById("deleteConfirmModal");
    if (deleteModalEl) {
        deleteModalEl.addEventListener("show.bs.modal", function (event) {
            const button = event.relatedTarget;
            const predictionId = button.getAttribute("data-id");
            const deleteForm = document.getElementById("deleteForm");
            if (deleteForm && predictionId) {
                deleteForm.action = `/history/${predictionId}/delete`;
                const modalIdText = document.getElementById("modalPredictionId");
                if (modalIdText) modalIdText.textContent = predictionId;
            }
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
});

/**
 * Applies sample presets to the prediction form for quick demonstrations.
 */
function applyPreset(presetType) {
    const presets = {
        apartment: {
            daily: 6.5,
            prev: 190.0,
            days: 30,
            tariff: 6.50,
            fixed: 40.0,
            additional: 5.0,
        },
        medium: {
            daily: 12.8,
            prev: 375.0,
            days: 30,
            tariff: 7.50,
            fixed: 50.0,
            additional: 5.0,
        },
        heavy: {
            daily: 26.5,
            prev: 780.0,
            days: 30,
            tariff: 9.00,
            fixed: 100.0,
            additional: 8.0,
        },
    };

    const data = presets[presetType];
    if (!data) return;

    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) {
            el.value = val;
            el.dispatchEvent(new Event("input"));
        }
    };

    setVal("average_daily_consumption_kwh", data.daily);
    setVal("previous_month_consumption_kwh", data.prev);
    setVal("billing_days", data.days);
    setVal("tariff_per_kwh", data.tariff);
    setVal("fixed_charges", data.fixed);
    setVal("additional_charge_percentage", data.additional);
}
