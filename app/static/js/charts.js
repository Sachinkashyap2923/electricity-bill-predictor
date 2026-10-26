/**
 * Chart.js Visualizations for Electricity Bill Predictor
 * Provides chart renderers for Dashboard and Model Evaluation pages.
 */

window.ElectricityCharts = {
    /**
     * Initializes the Dashboard Charts:
     * 1. Bill and Consumption History Trend (Dual Line)
     * 2. Usage Category Doughnut Chart (Low vs Moderate vs High)
     */
    initDashboardCharts: function (data) {
        // 1. History Trend Chart
        const historyCtx = document.getElementById("dashboardHistoryChart");
        if (historyCtx && data.chartLabels && data.chartLabels.length > 0) {
            new Chart(historyCtx, {
                type: "line",
                data: {
                    labels: data.chartLabels,
                    datasets: [
                        {
                            label: "Estimated Bill (₹)",
                            data: data.chartBills,
                            borderColor: "#2563eb",
                            backgroundColor: "rgba(37, 99, 235, 0.1)",
                            borderWidth: 2,
                            fill: true,
                            tension: 0.3,
                            yAxisID: "yBill",
                        },
                        {
                            label: "Predicted Consumption (kWh)",
                            data: data.chartConsumptions,
                            borderColor: "#0ea5e9",
                            backgroundColor: "rgba(14, 165, 233, 0.05)",
                            borderWidth: 2,
                            borderDash: [4, 4],
                            fill: false,
                            tension: 0.3,
                            yAxisID: "yKwh",
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: "index",
                        intersect: false,
                    },
                    scales: {
                        yBill: {
                            type: "linear",
                            display: true,
                            position: "left",
                            title: { display: true, text: "Estimated Bill (₹)" },
                        },
                        yKwh: {
                            type: "linear",
                            display: true,
                            position: "right",
                            grid: { drawOnChartArea: false },
                            title: { display: true, text: "Monthly kWh" },
                        },
                    },
                },
            });
        }

        // 2. Usage Category Doughnut Chart
        const categoryCtx = document.getElementById("dashboardCategoryChart");
        if (categoryCtx && data.categoryCounts) {
            new Chart(categoryCtx, {
                type: "doughnut",
                data: {
                    labels: ["Low (<150 kWh)", "Moderate (150-400 kWh)", "High (>400 kWh)"],
                    datasets: [
                        {
                            data: [
                                data.categoryCounts.Low || 0,
                                data.categoryCounts.Moderate || 0,
                                data.categoryCounts.High || 0,
                            ],
                            backgroundColor: ["#10b981", "#3b82f6", "#f59e0b"],
                            borderWidth: 2,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "bottom" },
                    },
                },
            });
        }
    },

    /**
     * Initializes the Model Evaluation Charts:
     * 1. Metrics Comparison Bar Chart (MAE & RMSE for LR vs RF)
     * 2. Actual vs Predicted Line/Scatter Comparison on Held-out Test Set
     */
    initEvaluationCharts: function (data) {
        // 1. Error Metrics Comparison (MAE & RMSE)
        const metricsCtx = document.getElementById("modelMetricsComparisonChart");
        if (metricsCtx && data.models) {
            const lr = data.models.linear_regression;
            const rf = data.models.random_forest;

            new Chart(metricsCtx, {
                type: "bar",
                data: {
                    labels: ["Mean Absolute Error (MAE)", "Root Mean Squared Error (RMSE)"],
                    datasets: [
                        {
                            label: "Linear Regression",
                            data: [lr.mae, lr.rmse],
                            backgroundColor: "rgba(37, 99, 235, 0.8)",
                            borderColor: "#1d4ed8",
                            borderWidth: 1,
                        },
                        {
                            label: "Random Forest Regressor",
                            data: [rf.mae, rf.rmse],
                            backgroundColor: "rgba(16, 185, 129, 0.8)",
                            borderColor: "#059669",
                            borderWidth: 1,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: "Error in kWh (Lower is Better)" },
                        },
                    },
                },
            });
        }

        // 2. Actual vs Predicted Comparison Chart
        const actualVsPredCtx = document.getElementById("actualVsPredictedChart");
        if (actualVsPredCtx && data.samples) {
            new Chart(actualVsPredCtx, {
                type: "line",
                data: {
                    labels: data.samples.indices,
                    datasets: [
                        {
                            label: "Actual Test Target (kWh)",
                            data: data.samples.actual,
                            borderColor: "#0f172a",
                            backgroundColor: "#0f172a",
                            borderWidth: 2.5,
                            pointRadius: 4,
                            fill: false,
                        },
                        {
                            label: "Linear Regression Prediction (kWh)",
                            data: data.samples.linear_regression,
                            borderColor: "#2563eb",
                            backgroundColor: "rgba(37, 99, 235, 0.2)",
                            borderWidth: 2,
                            borderDash: [3, 3],
                            pointRadius: 3,
                            fill: false,
                        },
                        {
                            label: "Random Forest Prediction (kWh)",
                            data: data.samples.random_forest,
                            borderColor: "#10b981",
                            backgroundColor: "rgba(16, 185, 129, 0.2)",
                            borderWidth: 2,
                            borderDash: [5, 5],
                            pointRadius: 3,
                            fill: false,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: "index",
                        intersect: false,
                    },
                    scales: {
                        y: {
                            title: { display: true, text: "Monthly Consumption (kWh)" },
                        },
                        x: {
                            ticks: { maxRotation: 45, minRotation: 45 },
                        },
                    },
                },
            });
        }
    },
};
